"""Fetch XAUUSD live spot + OHLC candles on D1/H4/H1/M15 (TwelveData).

Writes a single JSON blob to data/cache/<UTC timestamp>.json and prints the path.
Reads keys from config/.env.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "config" / ".env"
CACHE_DIR = ROOT / "data" / "cache"

TIMEFRAMES = {
    "D1": "1day",
    "H4": "4h",
    "H1": "1h",
    "M15": "15min",
}
CANDLE_COUNTS = {"D1": 120, "H4": 200, "H1": 200, "M15": 200}
SYMBOL_TD = "XAU/USD"
GOLDAPI_NET_ENDPOINTS = (
    ("https://app.goldapi.net/api/price/XAU/USD", "header"),
    ("https://app.goldapi.net/price/XAU/USD", "query"),
)
GOLDAPI_IO_ENDPOINT = "https://www.goldapi.io/api/XAU/USD"
PLACEHOLDER_KEYS = {"", "your_goldapi_key_here", "your_goldapi_net_key_here"}
DEFAULT_TWELVEDATA_RETRY_SECONDS = 65


def load_env(path: Path) -> dict[str, str]:
    """Read .env (if present) then overlay os.environ so CI secrets win."""
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if " #" in v and not (v.startswith('"') or v.startswith("'")):
                v = v.split(" #", 1)[0].strip()
            env[k.strip()] = v
    for k in ("GOLDAPI_NET_KEY", "GOLDAPI_KEY", "QUOTE_SOURCE", "TWELVEDATA_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    if "TWELVEDATA_KEY" not in env:
        sys.exit("TWELVEDATA_KEY required (config/.env or environment)")
    return env


USER_AGENT = "Mozilla/5.0 (Trading-Setup/1.0)"


def http_get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        preview = body[:160].replace("\n", " ")
        raise RuntimeError(f"expected JSON from {url}, got {preview!r}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object from spot API, got {type(data).__name__}")
    return data


def _require_price(data: dict, source: str) -> dict:
    if data.get("price") is None:
        raise RuntimeError(f"{source} response missing price")
    data.setdefault("source", source)
    return data


def fetch_spot_goldapi_net(key: str) -> dict:
    """Fetch XAU/USD from goldapi.net.

    The public docs show the query-param route, while another working setup used
    the /api/price route with an x-api-key header. Try both and require JSON.
    """
    errors: list[str] = []
    for base_url, auth_style in GOLDAPI_NET_ENDPOINTS:
        if auth_style == "header":
            url = base_url
            headers = {"x-api-key": key}
        else:
            query = urllib.parse.urlencode({"x-api-key": key})
            url = f"{base_url}?{query}"
            headers = None
        try:
            return _require_price(http_get_json(url, headers=headers), "goldapi.net")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{auth_style}: {exc}")
    raise RuntimeError("; ".join(errors))


def fetch_spot_goldapi_io(key: str) -> dict:
    data = http_get_json(
        GOLDAPI_IO_ENDPOINT,
        headers={"x-access-token": key, "Content-Type": "application/json"},
    )
    return _require_price(data, "goldapi.io")


def fetch_spot_twelvedata(key: str) -> dict:
    query = urllib.parse.urlencode({"symbol": SYMBOL_TD, "apikey": key})
    data = http_get_json(f"https://api.twelvedata.com/price?{query}")
    return _require_price(data, "twelvedata")


def _configured_key(env: dict[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    return "" if value in PLACEHOLDER_KEYS else value


def fetch_spot(env: dict[str, str]) -> dict:
    source = env.get("QUOTE_SOURCE", "auto").strip().lower()
    sources: list[tuple[str, str, Callable[[str], dict]]] = []
    if source in {"goldapi-net", "goldapinet"}:
        sources = [("goldapi.net", "GOLDAPI_NET_KEY", fetch_spot_goldapi_net)]
    elif source in {"goldapi", "goldapi-io", "goldapiio"}:
        sources = [("goldapi.io", "GOLDAPI_KEY", fetch_spot_goldapi_io)]
    elif source in {"twelvedata", "twelve-data"}:
        sources = [("TwelveData spot", "TWELVEDATA_KEY", fetch_spot_twelvedata)]
    elif source == "auto":
        sources = [
            ("goldapi.net", "GOLDAPI_NET_KEY", fetch_spot_goldapi_net),
            ("goldapi.io", "GOLDAPI_KEY", fetch_spot_goldapi_io),
        ]
    else:
        sys.exit("QUOTE_SOURCE must be auto, goldapi-net, goldapi-io, or twelvedata")

    errors: list[str] = []
    for label, key_name, fetcher in sources:
        key = _configured_key(env, key_name)
        if not key:
            errors.append(f"{label}: {key_name} not set")
            continue
        try:
            return fetcher(key)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
    raise RuntimeError("No spot source succeeded: " + " | ".join(errors))


def _is_twelvedata_rate_limit(message: str) -> bool:
    msg = message.lower()
    return "api credits" in msg or "current minute" in msg or "rate limit" in msg


def fetch_candles(tf_label: str, tf_api: str, count: int, key: str) -> dict:
    q = urllib.parse.urlencode(
        {"symbol": SYMBOL_TD, "interval": tf_api, "outputsize": count, "apikey": key}
    )
    url = f"https://api.twelvedata.com/time_series?{q}"
    retry_seconds = int(os.environ.get("TWELVEDATA_RETRY_SECONDS", DEFAULT_TWELVEDATA_RETRY_SECONDS))
    data = http_get_json(url)
    if data.get("status") == "error":
        message = data.get("message", "unknown error")
        if retry_seconds > 0 and _is_twelvedata_rate_limit(message):
            print(f"TwelveData rate limit for {tf_label}; waiting {retry_seconds}s then retrying...", file=sys.stderr)
            time.sleep(retry_seconds)
            data = http_get_json(url)
        if data.get("status") == "error":
            raise RuntimeError(f"TwelveData error for {tf_label}: {data.get('message')}")
    # Normalize oldest-first
    values = list(reversed(data.get("values", [])))
    return {
        "timeframe": tf_label,
        "candles": [
            {
                "t": v["datetime"],
                "o": float(v["open"]),
                "h": float(v["high"]),
                "l": float(v["low"]),
                "c": float(v["close"]),
            }
            for v in values
        ],
    }


def spot_from_candles(timeframes: dict, *, errors: str | None = None) -> dict:
    for label in ("M15", "H1", "H4", "D1"):
        candles = timeframes.get(label, {}).get("candles") or []
        if candles:
            last = candles[-1]
            spot = {
                "price": last["c"],
                "bid": None,
                "ask": None,
                "source": f"twelvedata_{label}_close",
                "time": last.get("t"),
            }
            if errors:
                spot["fallback_reason"] = errors[:500]
            return spot
    raise RuntimeError("No candle data available for spot fallback")


def main() -> None:
    env = load_env(ENV_PATH)
    td_key = env.get("TWELVEDATA_KEY", "")
    if not td_key or td_key == "your_twelvedata_key_here":
        sys.exit("TWELVEDATA_KEY not set in config/.env")

    now = datetime.now(timezone.utc)
    spot: dict | None = None
    spot_error: str | None = None
    try:
        spot = fetch_spot(env)
    except Exception as exc:  # noqa: BLE001
        spot_error = str(exc)
        print(f"Spot providers unavailable; will use latest candle close. {spot_error[:220]}", file=sys.stderr)

    payload: dict = {
        "fetched_at_utc": now.isoformat(),
        "symbol": "XAUUSD",
        "spot": {},
        "timeframes": {},
    }
    for label, api in TIMEFRAMES.items():
        payload["timeframes"][label] = fetch_candles(label, api, CANDLE_COUNTS[label], td_key)
    payload["spot"] = spot if spot is not None else spot_from_candles(payload["timeframes"], errors=spot_error)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    out = CACHE_DIR / f"{stamp}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest = CACHE_DIR / "latest.json"
    latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()

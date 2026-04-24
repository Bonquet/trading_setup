"""Fetch XAUUSD live spot (GoldAPI) + OHLC candles on D1/H4/H1/M15 (TwelveData).

Writes a single JSON blob to data/cache/<UTC timestamp>.json and prints the path.
Reads keys from config/.env.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
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


def load_env(path: Path) -> dict[str, str]:
    """Read .env (if present) then overlay os.environ so CI secrets win."""
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if " #" in v and not (v.startswith('"') or v.startswith("'")):
                v = v.split(" #", 1)[0].strip()
            env[k.strip()] = v
    for k in ("GOLDAPI_KEY", "TWELVEDATA_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    if "GOLDAPI_KEY" not in env or "TWELVEDATA_KEY" not in env:
        sys.exit("GOLDAPI_KEY and TWELVEDATA_KEY required (config/.env or environment)")
    return env


USER_AGENT = "Mozilla/5.0 (Trading-Setup/1.0)"


def http_get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_spot(key: str) -> dict:
    return http_get_json(
        "https://www.goldapi.io/api/XAU/USD",
        headers={"x-access-token": key, "Content-Type": "application/json"},
    )


def fetch_candles(tf_label: str, tf_api: str, count: int, key: str) -> dict:
    q = urllib.parse.urlencode(
        {"symbol": SYMBOL_TD, "interval": tf_api, "outputsize": count, "apikey": key}
    )
    data = http_get_json(f"https://api.twelvedata.com/time_series?{q}")
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


def main() -> None:
    env = load_env(ENV_PATH)
    gold_key = env.get("GOLDAPI_KEY", "")
    td_key = env.get("TWELVEDATA_KEY", "")
    if not gold_key or gold_key == "your_goldapi_key_here":
        sys.exit("GOLDAPI_KEY not set in config/.env")
    if not td_key or td_key == "your_twelvedata_key_here":
        sys.exit("TWELVEDATA_KEY not set in config/.env")

    now = datetime.now(timezone.utc)
    payload: dict = {
        "fetched_at_utc": now.isoformat(),
        "symbol": "XAUUSD",
        "spot": fetch_spot(gold_key),
        "timeframes": {},
    }
    for label, api in TIMEFRAMES.items():
        payload["timeframes"][label] = fetch_candles(label, api, CANDLE_COUNTS[label], td_key)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    out = CACHE_DIR / f"{stamp}.json"
    out.write_text(json.dumps(payload, indent=2))
    latest = CACHE_DIR / "latest.json"
    latest.write_text(json.dumps(payload, indent=2))
    print(str(out))


if __name__ == "__main__":
    main()

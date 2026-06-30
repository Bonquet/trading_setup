"""End-to-end health check for the XAUUSD trading bot.

Verifies:
  1. Python + required files/folders
  2. config/.env has required keys
  3. Selected gold spot API key works (goldapi.net preferred, GoldAPI.io fallback)
  4. TwelveData key works (1 candle fetch)
  5. Twilio creds authenticate (account GET — does NOT send a message)
  6. Optional: --send flag fires a real WhatsApp test message

Exit code 0 = all green, non-zero = at least one check failed.

Usage:
  python scripts/health_check.py
  python scripts/health_check.py --send   # also send a test WhatsApp
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "config" / ".env"
# Reply notifier is env-configurable (Telegram workflow sets NOTIFIER_SCRIPT).
NOTIFIER_NAME = os.environ.get("NOTIFIER_SCRIPT", "notify_whatsapp.py")

REQUIRED_FILES = [
    "CLAUDE.md",
    "strategy/playbook.md",
    "strategy/50ema_pullback.md",
    "memory/MEMORY_INDEX.md",
    "routines/london.md",
    "routines/ny.md",
    "journal/trades.md",
    "scripts/fetch_gold.py",
    "scripts/compute_levels.py",
    "scripts/generate_signal.py",
    "scripts/notify_whatsapp.py",
    "scripts/run_auto.py",
    "scripts/weekly_stats.py",
    ".github/workflows/trading-session.yml",
]
REQUIRED_DIRS = [
    "memory/trade_history",
    "memory/wins",
    "memory/losses",
    "memory/mistakes",
    "memory/market_profiles",
]
# Created at runtime if missing — not an error if absent.
RUNTIME_DIRS = ["data/cache"]

USER_AGENT = "Mozilla/5.0 (Trading-Setup/1.0)"

GREEN = "[OK]"
RED = "[FAIL]"
WARN = "[WARN]"


def load_env(path: Path) -> dict[str, str]:
    import os
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
    for k in (
        "GOLDAPI_NET_KEY", "GOLDAPI_KEY", "QUOTE_SOURCE", "TWELVEDATA_KEY", "WHATSAPP_BACKEND",
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET",
        "TWILIO_FROM", "TWILIO_TO",
    ):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def http_get(url: str, headers: dict | None = None, timeout: int = 15) -> tuple[int, str]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def check_files() -> list[str]:
    errs = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errs.append(f"missing file: {rel}")
    for rel in REQUIRED_DIRS:
        if not (ROOT / rel).is_dir():
            errs.append(f"missing dir: {rel}")
    # Auto-create runtime dirs so CI checkouts don't false-alarm.
    for rel in RUNTIME_DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)
    return errs


def check_env(env: dict) -> list[str]:
    errs = []
    for k in ("TWELVEDATA_KEY",):
        if not env.get(k):
            errs.append(f"{k} missing in config/.env")
    source = env.get("QUOTE_SOURCE", "auto").strip().lower()
    if source in {"goldapi-net", "goldapinet"}:
        if not env.get("GOLDAPI_NET_KEY"):
            errs.append("GOLDAPI_NET_KEY missing in config/.env")
    elif source in {"goldapi", "goldapi-io", "goldapiio"}:
        if not env.get("GOLDAPI_KEY"):
            errs.append("GOLDAPI_KEY missing in config/.env")
    elif source in {"twelvedata", "twelve-data"}:
        pass
    elif source == "auto":
        pass
    else:
        errs.append("QUOTE_SOURCE must be auto, goldapi-net, goldapi-io, or twelvedata")
    backend = env.get("WHATSAPP_BACKEND", "disabled").lower()
    if backend == "twilio":
        for k in ("TWILIO_ACCOUNT_SID", "TWILIO_FROM", "TWILIO_TO"):
            if not env.get(k):
                errs.append(f"{k} missing (required for twilio backend)")
        if not ((env.get("TWILIO_API_KEY_SID") and env.get("TWILIO_API_KEY_SECRET"))
                or env.get("TWILIO_AUTH_TOKEN")):
            errs.append("need TWILIO_API_KEY_SID+TWILIO_API_KEY_SECRET or TWILIO_AUTH_TOKEN")
    return errs


def _check_price_json(code: int, body: str, label: str) -> tuple[bool, str]:
    if code != 200:
        return False, f"HTTP {code}: {body[:200]}"
    try:
        j = json.loads(body)
        price = j.get("price") if isinstance(j, dict) else None
        if price is None:
            return False, f"{label} JSON missing price: {body[:200]}"
        return True, f"spot=${price}"
    except Exception:  # noqa: BLE001
        return False, f"bad JSON: {body[:200]}"


def check_goldapi_net(key: str) -> tuple[bool, str]:
    attempts = []
    code, body = http_get(
        "https://app.goldapi.net/api/price/XAU/USD",
        headers={"x-api-key": key},
    )
    ok, msg = _check_price_json(code, body, "GoldAPI.net header route")
    if ok:
        return ok, msg
    attempts.append(f"header route {msg}")

    q = urllib.parse.urlencode({"x-api-key": key})
    code, body = http_get(f"https://app.goldapi.net/price/XAU/USD?{q}")
    ok, msg = _check_price_json(code, body, "GoldAPI.net query route")
    if ok:
        return ok, msg
    attempts.append(f"query route {msg}")
    return False, "; ".join(attempts)


def check_goldapi_io(key: str) -> tuple[bool, str]:
    code, body = http_get(
        "https://www.goldapi.io/api/XAU/USD",
        headers={"x-access-token": key, "Content-Type": "application/json"},
    )
    return _check_price_json(code, body, "GoldAPI.io")


def check_twelvedata_spot(key: str) -> tuple[bool, str]:
    q = urllib.parse.urlencode({"symbol": "XAU/USD", "apikey": key})
    code, body = http_get(f"https://api.twelvedata.com/price?{q}")
    return _check_price_json(code, body, "TwelveData spot")


def spot_check_plan(env: dict) -> list[tuple[str, str, object]]:
    source = env.get("QUOTE_SOURCE", "auto").strip().lower()
    if source in {"goldapi-net", "goldapinet"}:
        return [("GoldAPI.net", "GOLDAPI_NET_KEY", check_goldapi_net)]
    if source in {"goldapi", "goldapi-io", "goldapiio"}:
        return [("GoldAPI.io", "GOLDAPI_KEY", check_goldapi_io)]
    if source in {"twelvedata", "twelve-data"}:
        return [("TwelveData spot", "TWELVEDATA_KEY", check_twelvedata_spot)]
    return [
        ("GoldAPI.net", "GOLDAPI_NET_KEY", check_goldapi_net),
        ("GoldAPI.io", "GOLDAPI_KEY", check_goldapi_io),
        ("TwelveData spot", "TWELVEDATA_KEY", check_twelvedata_spot),
    ]


def check_twelvedata(key: str) -> tuple[bool, str]:
    q = urllib.parse.urlencode({"symbol": "XAU/USD", "interval": "1h", "outputsize": 1, "apikey": key})
    code, body = http_get(f"https://api.twelvedata.com/time_series?{q}")
    if code != 200:
        return False, f"HTTP {code}: {body[:200]}"
    try:
        j = json.loads(body)
        if j.get("status") == "error":
            return False, j.get("message", "unknown error")
        vals = j.get("values") or []
        if not vals:
            return False, "no candles returned"
        return True, f"last close={vals[0].get('close')}"
    except Exception:  # noqa: BLE001
        return False, f"bad JSON: {body[:200]}"


def check_twilio(env: dict) -> tuple[bool, str]:
    sid = env.get("TWILIO_ACCOUNT_SID", "")
    api_sid = env.get("TWILIO_API_KEY_SID", "")
    api_secret = env.get("TWILIO_API_KEY_SECRET", "")
    tok = env.get("TWILIO_AUTH_TOKEN", "")
    if api_sid and api_secret:
        user, pw = api_sid, api_secret
    elif tok:
        user, pw = sid, tok
    else:
        return False, "no auth configured"
    auth = b64encode(f"{user}:{pw}".encode()).decode()
    code, body = http_get(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json",
        headers={"Authorization": f"Basic {auth}"},
    )
    if code != 200:
        return False, f"HTTP {code}: {body[:200]}"
    try:
        j = json.loads(body)
        return True, f"account status={j.get('status')} friendly_name={j.get('friendly_name')}"
    except Exception:  # noqa: BLE001
        return False, f"bad JSON: {body[:200]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="also send a live WhatsApp test message")
    ap.add_argument("--notify", action="store_true", help="always send a WhatsApp summary")
    ap.add_argument("--notify-on-fail", action="store_true", help="send WhatsApp only if something failed")
    args = ap.parse_args()

    print(f"Health check — {ROOT}")
    print("=" * 60)
    fails = 0
    summary_lines: list[str] = []

    def record(ok: bool, label: str, msg: str) -> None:
        summary_lines.append(f"{'OK' if ok else 'FAIL'} {label}: {msg}")

    # 1. Files
    errs = check_files()
    if errs:
        fails += len(errs)
        for e in errs:
            print(f"{RED} {e}")
        record(False, "Files", "; ".join(errs[:3]))
    else:
        print(f"{GREEN} all required files and dirs present ({len(REQUIRED_FILES)} files, {len(REQUIRED_DIRS)} dirs)")
        record(True, "Files", f"{len(REQUIRED_FILES)} files + {len(REQUIRED_DIRS)} dirs present")

    # 2. Env
    env = load_env(ENV_PATH)
    errs = check_env(env)
    if errs:
        fails += len(errs)
        for e in errs:
            print(f"{RED} {e}")
        record(False, "Env", "; ".join(errs[:3]))
    else:
        print(f"{GREEN} config/.env has required keys (backend={env.get('WHATSAPP_BACKEND')})")
        record(True, "Env", f"backend={env.get('WHATSAPP_BACKEND')}")

    # 3. Gold spot source
    spot_ok = False
    spot_attempted = False
    spot_errors: list[str] = []
    for label, key_name, checker in spot_check_plan(env):
        key = env.get(key_name)
        if not key:
            spot_errors.append(f"{label}: {key_name} missing")
            continue
        spot_attempted = True
        ok, msg = checker(key)  # type: ignore[operator]
        print(f"{GREEN if ok else RED} {label}: {msg}")
        record(ok, label, msg[:120])
        if ok:
            spot_ok = True
            break
        spot_errors.append(f"{label}: {msg[:120]}")
    if not spot_ok:
        if not spot_attempted:
            print(f"{RED} Gold spot: {'; '.join(spot_errors)}")
            record(False, "Gold spot", "; ".join(spot_errors))
        fails += 1

    # 4. TwelveData
    if env.get("TWELVEDATA_KEY"):
        ok, msg = check_twelvedata(env["TWELVEDATA_KEY"])
        print(f"{GREEN if ok else RED} TwelveData: {msg}")
        record(ok, "TwelveData", msg[:120])
        if not ok:
            fails += 1

    # 5. Twilio
    if env.get("WHATSAPP_BACKEND", "").lower() == "twilio" and env.get("TWILIO_ACCOUNT_SID"):
        ok, msg = check_twilio(env)
        print(f"{GREEN if ok else RED} Twilio auth: {msg}")
        record(ok, "Twilio", msg[:120])
        if not ok:
            fails += 1

    # 6. Optional live send
    if args.send:
        print("- Sending live WhatsApp test…")
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / NOTIFIER_NAME),
             "XAU bot — health_check test send"],
            cwd=str(ROOT),
        )
        if r.returncode == 0:
            print(f"{GREEN} WhatsApp send returned 0 (check your phone)")
        else:
            print(f"{RED} WhatsApp send failed (exit {r.returncode})")
            fails += 1

    print("=" * 60)
    overall_ok = fails == 0
    if overall_ok:
        print(f"{GREEN} ALL CHECKS PASSED")
    else:
        print(f"{RED} {fails} check(s) failed")

    # WhatsApp summary (always-on or fail-only)
    if args.notify or (args.notify_on_fail and not overall_ok):
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        header = "XAU bot health check — " + ("ALL GREEN" if overall_ok else f"{fails} FAILURE(S)")
        body = "\n".join(f"• {ln}" for ln in summary_lines)
        msg = f"{header}\n{ts}\n{body}"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts
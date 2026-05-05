"""Sync MT5 broker state into data/accounts.json.

For each account in accounts.json that has an `mt5` config block, this script:
  1. Logs into MT5 with that account's investor password (read-only)
  2. Pulls live balance, equity, open positions, and recently closed deals
  3. Updates data/accounts.json
  4. Optionally git-commits and pushes the changes

Each account in accounts.json should look like:
    "main": {
      "balance": 4897.15,
      "initial_balance": 5000.0,
      "currency": "USD",
      ...
      "mt5": {
        "login": 1234567,
        "server": "FTMO-Server",
        "password_env": "MT5_MAIN_INVESTOR_PWD"
      }
    }

The investor password is read from the env var named in `password_env`. Put it in
config/.env (gitignored), e.g.:
    MT5_MAIN_INVESTOR_PWD=yourReadOnlyPasswordHere

Auto-discovery mode: pass `--discover <login> <password> <server> <bot_name>` to
register a new MT5 account in accounts.json without editing JSON manually.

Requirements:
  - Windows + MT5 desktop terminal installed
  - pip install MetaTrader5
  - Investor (read-only) password for each account

Usage:
  python scripts/mt5_sync.py                 # sync all configured accounts once
  python scripts/mt5_sync.py --watch 300     # sync every 5 min (300s) forever
  python scripts/mt5_sync.py --once main     # sync only 'main'
  python scripts/mt5_sync.py --discover 1234567 PASSWORD FTMO-Server main
  python scripts/mt5_sync.py --commit        # also git commit + push after sync
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = ROOT / "data" / "accounts.json"
ENV_PATH = ROOT / "config" / ".env"

CONTRACT_SIZE = 100.0  # XAUUSD: 1 lot = 100 oz, $100 per $1 price move per lot


def load_env(path: Path) -> dict[str, str]:
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
    # Overlay process env (shell takes precedence)
    for k, v in os.environ.items():
        if k.startswith("MT5_"):
            env[k] = v
    return env


def load_accounts() -> dict:
    if not ACCOUNTS.exists():
        sys.exit(f"Missing {ACCOUNTS}")
    return json.loads(ACCOUNTS.read_text(encoding="utf-8"))


def save_accounts(data: dict) -> None:
    ACCOUNTS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def import_mt5():
    try:
        import MetaTrader5 as mt5
    except ImportError:
        sys.exit(
            "MetaTrader5 package not installed. Run:\n"
            "    pip install MetaTrader5\n"
            "Note: only works on Windows with MT5 terminal installed."
        )
    return mt5


def login(mt5, login_num: int, password: str, server: str) -> None:
    if not mt5.initialize():
        err = mt5.last_error()
        sys.exit(f"mt5.initialize() failed: {err}. Is MT5 terminal installed and running?")
    if not mt5.login(login=int(login_num), password=password, server=server):
        err = mt5.last_error()
        mt5.shutdown()
        sys.exit(f"mt5.login() failed for {login_num}@{server}: {err}")


def fetch_account_state(mt5) -> dict:
    """Pull balance, equity, margin, open positions, recent closed deals."""
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"account_info() returned None: {mt5.last_error()}")
    state = {
        "balance": float(info.balance),
        "equity": float(info.equity),
        "margin": float(info.margin),
        "margin_free": float(info.margin_free),
        "currency": info.currency,
        "leverage": info.leverage,
        "profit": float(info.profit),
        "name": info.name,
    }
    # Open positions
    positions = mt5.positions_get() or []
    state["positions"] = []
    for p in positions:
        state["positions"].append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": float(p.volume),
            "price_open": float(p.price_open),
            "sl": float(p.sl),
            "tp": float(p.tp),
            "price_current": float(p.price_current),
            "profit": float(p.profit),
            "swap": float(p.swap),
            "time_open": datetime.fromtimestamp(p.time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        })
    # Closed deals from last 14 days (so we catch anything we may have missed)
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=14)
    deals = mt5.history_deals_get(from_date, to_date) or []
    state["recent_deals"] = []
    for d in deals:
        # type 0=buy, 1=sell, 2=balance (deposit/withdraw); we only care about 0/1
        if d.type not in (0, 1):
            continue
        state["recent_deals"].append({
            "ticket": d.ticket,
            "position_id": d.position_id,
            "symbol": d.symbol,
            "type": "BUY" if d.type == 0 else "SELL",
            "volume": float(d.volume),
            "price": float(d.price),
            "profit": float(d.profit),
            "swap": float(d.swap),
            "commission": float(d.commission),
            "time": datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "comment": d.comment,
        })
    return state


def merge_into_accounts(data: dict, name: str, mt5_state: dict) -> None:
    """Update accounts.json[name] with live data from MT5."""
    acc = data["accounts"][name]
    acc["balance"] = round(mt5_state["balance"], 2)
    acc["equity"] = round(mt5_state["equity"], 2)
    acc["margin"] = round(mt5_state["margin"], 2)
    acc["margin_free"] = round(mt5_state["margin_free"], 2)
    acc["currency"] = mt5_state["currency"]
    acc["last_synced_at"] = now_iso()

    # Replace open positions (MT5 is source of truth for current state)
    new_open = []
    for p in mt5_state["positions"]:
        if not p["symbol"].upper().startswith("XAU"):
            continue  # only track XAU positions in the bot
        new_open.append({
            "id": f"mt5_{p['ticket']}",
            "account": name,
            "direction": p["type"],
            "entry": p["price_open"],
            "sl": p["sl"],
            "tp1": p["tp"],
            "tp2": p["tp"],
            "lots": p["volume"],
            "risk_usd": round(abs(p["price_open"] - p["sl"]) * p["volume"] * CONTRACT_SIZE, 2) if p["sl"] else 0,
            "risk_pct": acc.get("risk_pct", 1.0),
            "strategy": "mt5-imported",
            "opened_at": p["time_open"],
            "current_price": p["price_current"],
            "running_pnl": p["profit"],
        })

    # Remove existing open trades for this account; replace with MT5 truth
    data["open"] = [t for t in data.get("open", []) if t.get("account") != name] + new_open

    # Sync closed deals: add any not already in closed[]
    existing_ids = {t.get("id") for t in data.get("closed", [])}
    for d in mt5_state["recent_deals"]:
        if not d["symbol"].upper().startswith("XAU"):
            continue
        deal_id = f"mt5_{d['ticket']}"
        if deal_id in existing_ids:
            continue
        # Only append CLOSE deals (deals that closed a position have non-zero profit typically)
        if d["profit"] == 0 and d["swap"] == 0 and d["commission"] == 0:
            continue
        data.setdefault("closed", []).append({
            "id": deal_id,
            "account": name,
            "direction": d["type"],
            "entry": 0,  # opening price not in deal record; would need position_get_history
            "sl": 0,
            "tp1": 0,
            "tp2": 0,
            "lots": d["volume"],
            "exit": d["price"],
            "pnl_usd": round(d["profit"] + d["swap"] + d["commission"], 2),
            "r": 0,  # can't compute without entry/sl
            "status": "win" if d["profit"] > 0 else ("loss" if d["profit"] < 0 else "breakeven"),
            "strategy": "mt5-imported",
            "closed_at": d["time"],
            "reason": d["comment"] or "",
            "mt5_ticket": d["ticket"],
        })


def sync_account(mt5, env: dict, data: dict, name: str) -> bool:
    """Sync one account. Returns True if successful."""
    acc = data["accounts"].get(name)
    if not acc:
        print(f"  [{name}] not found in accounts.json")
        return False
    cfg = acc.get("mt5")
    if not cfg:
        print(f"  [{name}] no mt5 config block, skipping")
        return False
    login_num = cfg.get("login")
    server = cfg.get("server")
    pwd_env = cfg.get("password_env")
    if not (login_num and server and pwd_env):
        print(f"  [{name}] mt5 config incomplete (need login, server, password_env)")
        return False
    password = env.get(pwd_env, "")
    if not password:
        print(f"  [{name}] env var {pwd_env} is empty — set it in config/.env")
        return False

    print(f"  [{name}] logging in as {login_num}@{server}…")
    login(mt5, login_num, password, server)
    try:
        state = fetch_account_state(mt5)
        merge_into_accounts(data, name, state)
        print(f"  [{name}] balance ${state['balance']:.2f} equity ${state['equity']:.2f} "
              f"open positions {len([p for p in state['positions'] if p['symbol'].upper().startswith('XAU')])}")
        return True
    finally:
        mt5.shutdown()


def discover(login_num: int, password: str, server: str, bot_name: str) -> None:
    """Add a new MT5 account to accounts.json and config/.env (if writable)."""
    data = load_accounts()
    pwd_env = f"MT5_{bot_name.upper()}_INVESTOR_PWD"

    # Probe MT5 once to verify creds + initial balance
    mt5 = import_mt5()
    print(f"Probing MT5 with login {login_num}@{server}…")
    login(mt5, login_num, password, server)
    info = mt5.account_info()
    if info is None:
        mt5.shutdown()
        sys.exit(f"account_info() failed: {mt5.last_error()}")
    print(f"  → {info.name} | balance ${info.balance:.2f} | currency {info.currency}")
    mt5.shutdown()

    # Add to accounts.json
    if bot_name not in data["accounts"]:
        data["accounts"][bot_name] = {
            "balance": float(info.balance),
            "initial_balance": float(info.balance),
            "currency": info.currency,
            "prop_firm": True,
            "max_loss_usd": round(float(info.balance) * 0.04, 2),  # default 4% daily DD
            "max_risk_per_trade_usd": round(float(info.balance) * 0.01, 2),  # 1% per trade
            "high_conviction_risk_usd": round(float(info.balance) * 0.02, 2),  # 2%
            "style": "swing",
            "risk_pct": 1.0,
        }
    data["accounts"][bot_name]["mt5"] = {
        "login": int(login_num),
        "server": server,
        "password_env": pwd_env,
    }
    if not data.get("active"):
        data["active"] = bot_name
    save_accounts(data)
    print(f"\nRegistered '{bot_name}' in accounts.json with mt5 block.")
    print(f"\nNext: add this line to {ENV_PATH}:")
    print(f"  {pwd_env}={password}")
    print("\n(then run: python scripts/mt5_sync.py)")


def commit_and_push() -> None:
    cwd = str(ROOT)
    subprocess.run(["git", "config", "user.name", "mt5-sync"], cwd=cwd, check=False)
    subprocess.run(["git", "config", "user.email", "mt5-sync@local"], cwd=cwd, check=False)
    subprocess.run(["git", "add", "data/accounts.json"], cwd=cwd, check=False)
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd)
    if r.returncode == 0:
        print("  no changes to commit")
        return
    subprocess.run(["git", "commit", "-m", f"mt5-sync {now_iso()}"], cwd=cwd, check=False)
    push = subprocess.run(["git", "push"], cwd=cwd)
    if push.returncode != 0:
        print("  git push failed (continuing — local accounts.json is updated)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=int, default=0, help="loop forever, syncing every N seconds")
    ap.add_argument("--once", type=str, default=None, help="sync only this account name")
    ap.add_argument("--commit", action="store_true", help="git commit + push after each sync")
    ap.add_argument("--discover", nargs=4, metavar=("LOGIN", "PASSWORD", "SERVER", "BOT_NAME"),
                    help="register a new MT5 account in accounts.json")
    args = ap.parse_args()

    if args.discover:
        login_num, password, server, bot_name = args.discover
        discover(int(login_num), password, server, bot_name)
        return

    env = load_env(ENV_PATH)

    while True:
        data = load_accounts()
        names = [args.once] if args.once else [n for n, a in data["accounts"].items() if a.get("mt5")]
        if not names:
            print("No accounts have an mt5 block. Run with --discover to add one.")
            return

        print(f"\n[{now_iso()}] Syncing {len(names)} MT5 account(s)…")
        mt5 = import_mt5()
        for name in names:
            try:
                sync_account(mt5, env, data, name)
            except Exception as e:  # noqa: BLE001
                print(f"  [{name}] error: {e}")
        save_accounts(data)
        if args.commit:
            commit_and_push()
        print(f"  done. accounts.json updated.")

        if args.watch <= 0:
            return
        print(f"  sleeping {args.watch}s…")
        time.sleep(args.watch)


if __name__ == "__main__":
    main()

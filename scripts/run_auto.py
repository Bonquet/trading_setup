"""Fully automatic session runner.

Pipeline:
  fetch_gold.py        -> data/cache/latest.json
  compute_levels.py    -> data/cache/levels.json
  generate_signal.py   -> data/cache/signal.json   (or "No Trade" + exit 10)
  notify_whatsapp.py   <- called ONLY if a valid signal exists

Usage:
  python scripts/run_auto.py [session_label] [account_size]

session_label is passed through for logging only (e.g. "london", "ny").
account_size defaults to 10000.

Designed for GitHub Actions cron — exits 0 on any terminal state (signal or no-trade)
so CI doesn't mark "No Trade" runs as failures.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SIGNAL = ROOT / "data" / "cache" / "signal.json"
JOURNAL = ROOT / "journal" / "trades.md"


def run(cmd: list[str], *, allow_codes: tuple[int, ...] = (0,)) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode not in allow_codes:
        sys.exit(r.returncode)
    return r.returncode


def build_message(sig: dict, session: str) -> str:
    return (
        f"XAU {sig['direction']} @ {sig['entry']}\n"
        f"SL {sig['stop_loss']} | TP {sig['tp2']}\n"
        f"RR {sig['rr_to_tp2']}R | {sig['lots']} lots @ 1% risk\n"
        f"Strategy: {sig['strategy']} ({session})\n"
        f"D1 {sig['confluence']['D1_position']}, H4 {sig['confluence']['H4_position']}, "
        f"W%R {sig['confluence']['williams_r14']}, Stoch {sig['confluence']['stoch_k']}"
    )


def build_content_variables(sig: dict) -> str:
    """For a custom Twilio template expecting 1..6 variables."""
    return json.dumps({
        "1": sig["direction"],
        "2": str(sig["entry"]),
        "3": str(sig["stop_loss"]),
        "4": str(sig["tp2"]),
        "5": str(sig["rr_to_tp2"]),
        "6": sig["strategy"],
    })


def append_journal(sig: dict, session: str) -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    if not JOURNAL.exists():
        JOURNAL.write_text("# XAUUSD Trade Journal\n\n")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = (
        f"\n### {ts} — {sig['direction']} @ {sig['entry']}\n"
        f"- Session: {session}\n"
        f"- Strategy: {sig['strategy']}\n"
        f"- SL: {sig['stop_loss']} | TP1: {sig['tp1']} | TP2: {sig['tp2']}\n"
        f"- RR: {sig['rr_to_tp2']}R | Size: {sig['lots']} lots | Risk: 1% of ${sig['account']}\n"
        f"- Confluence: {sig['confluence']}\n"
        f"- Outcome: pending\n"
    )
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(entry)


def resolve_account_balance(cli_arg: str) -> tuple[str, float]:
    """Return (account_name, balance_usd) preferring the active account in accounts.json."""
    state = ROOT / "data" / "accounts.json"
    if state.exists():
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            name = data.get("active")
            if name and name in data.get("accounts", {}):
                return name, float(data["accounts"][name]["balance"])
        except Exception as e:  # noqa: BLE001
            print(f"(accounts.json unreadable: {e} — falling back to CLI arg)")
    return "default", float(cli_arg)


def build_no_trade_message(session: str, levels: dict, signal_payload: dict, acct_name: str, balance: float) -> str:
    """Diagnostic message for on-demand /best /london /ny that get No Trade."""
    spot = levels.get("spot") or levels.get("spot_price")
    tfs = levels.get("timeframes", {})
    def pos(tf: str) -> str:
        return tfs.get(tf, {}).get("position_vs_channel", "?")
    reason = signal_payload.get("reason", "no setup")
    return (
        f"XAU /{session} — No Trade\n"
        f"[{acct_name} ${balance:,.0f}]\n"
        f"Spot: ${spot}\n"
        f"D1: {pos('D1')} | H4: {pos('H4')}\n"
        f"H1: {pos('H1')} | M15: {pos('M15')}\n"
        f"Reason: {reason}\n"
        f"(bot is alive — discipline rule fired)"
    )


def main() -> None:
    session = sys.argv[1] if len(sys.argv) > 1 else "auto"
    account_cli = sys.argv[2] if len(sys.argv) > 2 else "10000"
    py = sys.executable

    # When invoked from a slash command (whatsapp-command.yml sets ON_DEMAND=1),
    # always reply — even on No Trade. Cron stays silent on No Trade by default.
    on_demand = os.environ.get("ON_DEMAND") == "1"

    acct_name, balance = resolve_account_balance(account_cli)
    print(f"Sizing against account '{acct_name}' balance ${balance:,.2f}")

    run([py, str(SCRIPTS / "fetch_gold.py")])
    run([py, str(SCRIPTS / "compute_levels.py")])
    # generate_signal exits 10 for No Trade; that's a clean terminal state
    code = run([py, str(SCRIPTS / "generate_signal.py"), str(balance)], allow_codes=(0, 10))
    if code == 10:
        if on_demand:
            try:
                levels = json.loads((ROOT / "data" / "cache" / "levels.json").read_text())
                payload = json.loads(SIGNAL.read_text()) if SIGNAL.exists() else {}
                msg = build_no_trade_message(session, levels, payload, acct_name, balance)
                subprocess.run([py, str(SCRIPTS / "notify_whatsapp.py"), msg], cwd=str(ROOT), check=False)
            except Exception as e:  # noqa: BLE001
                print(f"(no-trade notify failed: {e})")
        print("No signal to notify. Exiting cleanly.")
        return

    sig = json.loads(SIGNAL.read_text())
    msg = build_message(sig, session)
    # Prefix message with account context
    msg = f"[{acct_name} ${balance:,.0f}]\n" + msg

    # If a custom Twilio template is configured, inject variables at runtime
    env_overlay = os.environ.copy()
    if env_overlay.get("TWILIO_CONTENT_SID"):
        env_overlay["TWILIO_CONTENT_VARIABLES"] = build_content_variables(sig)

    print(f"\n$ notify_whatsapp.py ...")
    r = subprocess.run(
        [py, str(SCRIPTS / "notify_whatsapp.py"), msg],
        cwd=str(ROOT),
        env=env_overlay,
    )
    if r.returncode != 0:
        print(f"Notifier returned {r.returncode} (non-fatal).")

    append_journal(sig, session)

    # Record open trade against active account (if one is configured)
    if acct_name != "default":
        try:
            subprocess.run(
                [py, str(SCRIPTS / "accounts.py"), "open",
                 acct_name, sig["direction"], str(sig["entry"]), str(sig["stop_loss"]),
                 str(sig["tp1"]), str(sig["tp2"]), sig["strategy"], "1.0"],
                cwd=str(ROOT), check=False,
            )
        except Exception as e:  # noqa: BLE001
            print(f"(accounts.py open failed: {e} — non-fatal)")

    print("Done.")


if __name__ == "__main__":
    main()

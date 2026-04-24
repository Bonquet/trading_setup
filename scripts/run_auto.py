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


def main() -> None:
    session = sys.argv[1] if len(sys.argv) > 1 else "auto"
    account = sys.argv[2] if len(sys.argv) > 2 else "10000"
    py = sys.executable

    run([py, str(SCRIPTS / "fetch_gold.py")])
    run([py, str(SCRIPTS / "compute_levels.py")])
    # generate_signal exits 10 for No Trade; that's a clean terminal state
    code = run([py, str(SCRIPTS / "generate_signal.py"), account], allow_codes=(0, 10))
    if code == 10:
        print("No signal to notify. Exiting cleanly.")
        return

    sig = json.loads(SIGNAL.read_text())
    msg = build_message(sig, session)

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
    print("Done.")


if __name__ == "__main__":
    main()

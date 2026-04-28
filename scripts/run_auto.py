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


def build_message(sig: dict, session: str, levels: dict | None = None) -> str:
    """Detailed multi-section signal message — header + WHY + entry plan."""
    primary = sig.get("primary_tf", "H4")
    bias_tf = sig.get("bias_tf", "D1")
    stop_tf = sig.get("stop_tf", "H1")
    style_name = sig.get("style", "intraday")

    conf = sig["confluence"]
    bias_pos = conf.get(f"{bias_tf}_position", "?")
    primary_pos = conf.get(f"{primary}_position", "?")
    wr = conf["williams_r14"]
    k = conf["stoch_k"]
    direction = sig["direction"]

    # Plain-English explanation
    bias = "uptrend" if direction == "BUY" else "downtrend"
    side_word = "above" if direction == "BUY" else "below"
    pivot_target = "R1/R2" if direction == "BUY" else "S1/S2"
    pivot_used = "pivot target" if sig.get("pivot_target_used") else "fixed 2R"

    # Pull live tf data if levels provided (for richer reasoning)
    stop_atr_str = primary_atr_str = swing = ""
    if levels:
        tfs = levels.get("timeframes", {})
        if tfs.get(stop_tf, {}).get("atr14"):
            stop_atr_str = f", {stop_tf} ATR {round(tfs[stop_tf]['atr14'],1)}"
        if tfs.get(primary, {}).get("atr14"):
            primary_atr_str = f", {primary} ATR {round(tfs[primary]['atr14'],1)}"
        sw = tfs.get(stop_tf, {}).get("last_swing_low" if direction == "BUY" else "last_swing_high")
        if sw:
            swing = f", {stop_tf} swing {'low' if direction=='BUY' else 'high'} {round(sw,2)}"

    cap_src = sig.get("cap_source", "")
    cap_str = f" — capped by {cap_src}" if cap_src else ""

    return (
        f"XAU {direction} @ {sig['entry']}  [{style_name}]\n"
        f"SL {sig['stop_loss']} | TP {sig['tp2']}\n"
        f"RR {sig['rr_to_tp2']}R | {sig['lots']} lots | risk ${sig.get('risk_usd','?')}{cap_str}\n"
        f"Strategy: {sig['strategy']} ({session})\n"
        f"\n"
        f"WHY THIS TRADE:\n"
        f"• HTF bias confirmed: {bias_tf} {bias_pos} AND {primary} {primary_pos} — both {side_word} their 50 EMA "
        f"channels, so we are with the {bias}, not fighting it.\n"
        f"• Momentum firing: Williams %R {wr} on {primary} is past the trigger threshold, "
        f"meaning price is in the impulsive part of the move (not exhausted).\n"
        f"• Stochastic K {k} crossed its signal line — timing confirmation that "
        f"{primary} is actually pushing now, not stalling.\n"
        f"• Stop placed {('below' if direction=='BUY' else 'above')} the {stop_tf} last swing "
        f"{('low' if direction=='BUY' else 'high')} with an ATR buffer "
        f"({sig.get('stop_distance','?')} pts){swing}{stop_atr_str}{primary_atr_str}.\n"
        f"• Target: {pivot_used} toward {pivot_target} — RR {sig['rr_to_tp2']}R guaranteed "
        f"by the engine's ≥2R gate.\n"
        f"\n"
        f"INVALIDATION: stop hit, OR {bias_tf}/{primary} close back inside their 50 EMA channel.\n"
        f"\n"
        f"Reply /took <acct> [lots] when you take it, /close win|loss|be when it resolves."
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


def resolve_account(cli_arg: str) -> tuple[str, dict]:
    """Return (account_name, account_dict) using accounts.json active account.
    Falls back to a synthetic account using the CLI balance arg if no state exists.
    """
    state = ROOT / "data" / "accounts.json"
    if state.exists():
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            name = data.get("active")
            if name and name in data.get("accounts", {}):
                return name, data["accounts"][name]
        except Exception as e:  # noqa: BLE001
            print(f"(accounts.json unreadable: {e} — falling back to CLI arg)")
    return "default", {
        "balance": float(cli_arg),
        "risk_pct": 1.0,
        "style": "intraday",
        "max_risk_per_trade_usd": 0.0,
    }


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

    # On-demand (slash commands) always replies. Cron also notifies on no-trade
    # (heartbeat) unless QUIET_NO_TRADE=1 is set.
    on_demand = os.environ.get("ON_DEMAND") == "1"
    notify_no_trade = on_demand or os.environ.get("QUIET_NO_TRADE") != "1"

    acct_name, acct = resolve_account("10000" if account_cli is None else account_cli)
    balance = float(acct.get("balance", 10000.0))
    risk_pct_decimal = float(acct.get("risk_pct", 1.0)) / 100.0
    style = (acct.get("style") or "intraday").lower()
    max_risk_usd = float(acct.get("max_risk_per_trade_usd", 0.0))
    print(f"Sizing: account='{acct_name}' bal=${balance:,.2f} risk={risk_pct_decimal*100}% "
          f"style={style} cap=${max_risk_usd or 'none'}")

    run([py, str(SCRIPTS / "fetch_gold.py")])
    run([py, str(SCRIPTS / "compute_levels.py")])
    # generate_signal exits 10 for No Trade; that's a clean terminal state
    code = run([
        py, str(SCRIPTS / "generate_signal.py"),
        str(balance), str(risk_pct_decimal), str(max_risk_usd),
        f"--style={style}",
    ], allow_codes=(0, 10))
    if code == 10:
        if notify_no_trade:
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
    levels_data = None
    try:
        levels_data = json.loads((ROOT / "data" / "cache" / "levels.json").read_text())
    except Exception:  # noqa: BLE001
        pass
    msg = build_message(sig, session, levels_data)
    # Prefix message with account context (incl. prop firm DD buffer if set)
    buf_str = ""
    if acct.get("max_loss_usd"):
        used = max(0.0, float(acct.get("initial_balance", balance)) - balance)
        remaining = float(acct["max_loss_usd"]) - used
        buf_str = f" • DD buffer ${remaining:,.0f}/${acct['max_loss_usd']:,.0f}"
    msg = f"[{acct_name} ${balance:,.0f} • {round(risk_pct_decimal*100,1)}%{buf_str}]\n" + msg

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
                 str(sig["tp1"]), str(sig["tp2"]), sig["strategy"], str(risk_pct_decimal * 100)],
                cwd=str(ROOT), check=False,
            )
        except Exception as e:  # noqa: BLE001
            print(f"(accounts.py open failed: {e} — non-fatal)")

    print("Done.")


if __name__ == "__main__":
    main()

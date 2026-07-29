"""Track staged targets and close XAUUSD signals at final TP or SL.

The monitor reads the persisted open trades in data/accounts.json, checks recent
five-minute XAU/USD candles, sends compact Telegram group milestone updates, and
moves each trade into closed history independently. It is safe to run repeatedly.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import accounts
from fetch_gold import ENV_PATH, fetch_candles, load_env

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "journal" / "trades.md"
MEMORY = ROOT / "memory"
MONITOR_CANDLES = 500


def candle_events(trade: dict, candles: list[dict]) -> list[dict]:
    """Return newly observed target/SL events in chronological order."""
    direction = trade["direction"].upper()
    sl = float(trade["sl"])
    opened_at = parse_time(trade.get("opened_at"))
    targets = accounts.target_levels(trade)
    final_name = targets[-1][0]
    already_hit = {str(name).lower() for name in (trade.get("target_hits") or {})}
    events: list[dict] = []

    for candle in candles:
        candle_at = parse_time(candle.get("t"))
        if opened_at and candle_at and candle_at < opened_at:
            continue
        high = float(candle["h"])
        low = float(candle["l"])
        sl_hit = high >= sl if direction == "SELL" else low <= sl
        observed_at = str(candle.get("t") or "")
        reached = [
            (name, price) for name, price in targets
            if name.lower() not in already_hit
            and (low <= price if direction == "SELL" else high >= price)
        ]

        if sl_hit and reached:
            # A five-minute candle cannot reveal ordering. Record the conservative outcome.
            events.append({"kind": "sl", "price": sl, "observed_at": observed_at})
            return events
        if sl_hit:
            events.append({"kind": "sl", "price": sl, "observed_at": observed_at})
            return events

        for name, price in reached:
            events.append({
                "kind": "target",
                "name": name,
                "price": price,
                "observed_at": observed_at,
                "final": name == final_name,
            })
            already_hit.add(name.lower())
            if name == final_name:
                return events
    return events


def candle_outcome(trade: dict, candles: list[dict]) -> tuple[str, float, str] | None:
    """Backward-compatible final outcome helper used by tests and callers."""
    for event in candle_events(trade, candles):
        if event["kind"] == "sl":
            return "loss", float(event["price"]), str(event["observed_at"])
        if event.get("final"):
            return "win", float(event["price"]), str(event["observed_at"])
    return None


def parse_time(value: object) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def result_message(trade: dict, status: str, exit_price: float) -> str:
    level = "FINAL TP HIT" if status == "win" else "SL HIT"
    level_name = "TP" if status == "win" else "SL"
    return (
        f"XAUUSD {trade['direction'].upper()} - {level}\n"
        f"Entry: {float(trade['entry']):.2f}\n"
        f"{level_name}: {float(exit_price):.2f}"
    )


def target_message(trade: dict, name: str, price: float) -> str:
    return (
        f"XAUUSD {trade['direction'].upper()} - {name.upper()} HIT\n"
        f"Entry: {float(trade['entry']):.2f}\n"
        f"{name.upper()}: {float(price):.2f}"
    )


def record_target_hit(trade: dict, event: dict) -> None:
    key = str(event["name"]).lower()
    hits = trade.setdefault("target_hits", {})
    hits.setdefault(key, {
        "name": str(event["name"]).upper(),
        "price": float(event["price"]),
        "observed_at": str(event.get("observed_at") or ""),
        "notified_at": None,
    })


def close_trade(
    data: dict,
    trade: dict,
    status: str,
    exit_price: float,
    observed_at: str,
    final_level: str | None = None,
) -> dict:
    pnl = accounts.pnl_of(trade["direction"], float(trade["entry"]), exit_price, float(trade["lots"]))
    risk_usd = float(trade.get("risk_usd") or 0)
    closed = dict(trade)
    closed.update({
        "exit": exit_price,
        "pnl_usd": pnl,
        "r": round(pnl / risk_usd, 2) if risk_usd else 0.0,
        "status": status,
        "closed_at": accounts.now_iso(),
        "level_observed_at": observed_at,
        "reason": f"{final_level or 'TP'} reached" if status == "win" else "SL reached",
        "result_notified_at": None,
    })
    data["open"].remove(trade)
    data["closed"].append(closed)
    account = data.get("accounts", {}).get(trade.get("account"))
    if account is not None:
        account["balance"] = round(float(account["balance"]) + pnl, 2)
    return closed


def notify_pending(data: dict, *, dry_run: bool = False) -> int:
    sent = 0
    all_trades = list(data.get("open", [])) + list(data.get("closed", []))

    pending_targets: dict[tuple[str, str], list[tuple[dict, dict]]] = {}
    for trade in all_trades:
        signal_key = str(trade.get("signal_id") or trade.get("id"))
        for hit in (trade.get("target_hits") or {}).values():
            if hit.get("notified_at") is not None:
                continue
            name = str(hit.get("name") or "TP").upper()
            pending_targets.setdefault((signal_key, name), []).append((trade, hit))

    for related in pending_targets.values():
        trade, hit = related[0]
        message = target_message(trade, str(hit["name"]), float(hit["price"]))
        if dry_run:
            print(f"DRY RUN notification:\n{message}")
            continue
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "notify_telegram.py"), "--signal", message],
            cwd=str(ROOT), check=False,
        )
        if proc.returncode == 0:
            notified_at = accounts.now_iso()
            for item, item_hit in related:
                item_hit["notified_at"] = notified_at
                final_name = accounts.target_levels(item)[-1][0]
                if item.get("status") == "win" and str(item_hit["name"]).upper() == final_name:
                    item["result_notified_at"] = notified_at
            sent += 1
        else:
            print(f"Telegram target notification failed for #{trade.get('id', '?')}.", file=sys.stderr)

    pending_results: dict[str, list[dict]] = {}
    for trade in data.get("closed", []):
        if trade.get("result_notified_at") is not None:
            continue
        if not str(trade.get("reason") or "").endswith("reached"):
            continue
        final_name = accounts.target_levels(trade)[-1][0].lower()
        if trade.get("status") == "win" and final_name in (trade.get("target_hits") or {}):
            # The named final-target alert above is the result notification.
            continue
        key = str(trade.get("signal_id") or trade.get("id"))
        pending_results.setdefault(key, []).append(trade)

    for related in pending_results.values():
        trade = related[0]
        message = result_message(trade, trade["status"], float(trade["exit"]))
        if dry_run:
            print(f"DRY RUN notification:\n{message}")
            continue
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "notify_telegram.py"), "--signal", message],
            cwd=str(ROOT), check=False,
        )
        if proc.returncode == 0:
            notified_at = accounts.now_iso()
            for item in related:
                item["result_notified_at"] = notified_at
            sent += 1
        else:
            print(f"Telegram result notification failed for #{trade.get('id', '?')}.", file=sys.stderr)
    return sent


def append_journal(closed: dict) -> None:
    if not JOURNAL.exists():
        return
    level = accounts.target_levels(closed)[-1][0] if closed["status"] == "win" else "SL"
    block = (
        f"\n### {closed['closed_at']} - CLOSED {closed['direction']} #{closed['id']}\n"
        f"- Entry: {closed['entry']} | Exit: {closed['exit']} ({level} hit)\n"
        f"- Targets: {accounts.format_targets(closed)}\n"
        f"- Outcome: {closed['status']} | {closed['r']}R | P&L: ${closed['pnl_usd']:.2f}\n"
    )
    with JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(block)


def write_memory(closed: dict) -> None:
    date = closed["closed_at"][:10]
    status = closed["status"]
    trade_id = str(closed["id"]).replace(":", "").replace("-", "")
    filename = f"{date}_XAUUSD_50ema_williams_{status}_{trade_id}.md"
    content = (
        f"# XAUUSD 50 EMA Williams - {status.upper()}\n\n"
        f"- Trade ID: {closed['id']}\n"
        f"- Direction: {closed['direction']}\n"
        f"- Entry: {closed['entry']}\n"
        f"- SL: {closed['sl']}\n"
        f"- Targets: {accounts.format_targets(closed)}\n"
        f"- Exit: {closed['exit']}\n"
        f"- Result: {closed['r']}R (${closed['pnl_usd']:.2f})\n"
        f"- Opened: {closed.get('opened_at', '?')}\n"
        f"- Closed: {closed['closed_at']}\n\n"
        "## Process Review\n\n"
        "- Market and strategy passed the automated trend and momentum filters at entry.\n"
        "- Stop and target were generated from the configured structure/ATR rules.\n"
        "- Manual execution quality and discretionary rule adherence are not observable by the monitor.\n"
    )
    destinations = [MEMORY / "trade_history" / filename]
    destinations.append(MEMORY / ("wins" if status == "win" else "losses") / filename)
    for path in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="detect outcomes without writing or notifying")
    args = parser.parse_args()

    data = accounts.load()
    open_xau = [
        trade for trade in data.get("open", [])
        if (trade.get("instrument") or "XAUUSD").upper() == "XAUUSD"
    ]
    if not open_xau:
        changed = notify_pending(data, dry_run=args.dry_run)
        if changed and not args.dry_run:
            accounts.save(data)
        print("No active XAUUSD trade to monitor.")
        return

    env = load_env(ENV_PATH)
    key = env.get("TWELVEDATA_KEY", "").strip()
    if not key or key == "your_twelvedata_key_here":
        raise SystemExit("TWELVEDATA_KEY required for trade monitoring")
    candles = fetch_candles("M5", "5min", MONITOR_CANDLES, key, timezone_name="UTC")["candles"]
    if not candles:
        raise SystemExit("Trade monitor received no XAUUSD candles")

    closed_now: list[dict] = []
    milestones_now = 0
    state_changed = False
    for trade in list(open_xau):
        events = candle_events(trade, candles)
        closing_event = None
        for event in events:
            if event["kind"] == "target":
                print(
                    f"{event['name']} #{trade.get('id', '?')} at {event['price']} "
                    f"({event['observed_at']} UTC)"
                )
                milestones_now += 1
                if not args.dry_run:
                    record_target_hit(trade, event)
                    state_changed = True
                if event.get("final"):
                    closing_event = event
                    break
            else:
                closing_event = event
                break

        if closing_event is None:
            last = candles[-1]
            print(
                f"ACTIVE #{trade.get('id', '?')} {trade['direction']} @ {trade['entry']} - "
                f"last {last['c']} ({last['t']} UTC), SL {trade['sl']}, "
                f"{accounts.format_targets(trade)}"
            )
            continue

        if closing_event["kind"] == "sl":
            status = "loss"
            final_level = None
            print(
                f"LOSS #{trade.get('id', '?')} at {closing_event['price']} "
                f"({closing_event['observed_at']} UTC)"
            )
        else:
            status = "win"
            final_level = str(closing_event["name"]).upper()

        if not args.dry_run:
            closed_now.append(
                close_trade(
                    data,
                    trade,
                    status,
                    float(closing_event["price"]),
                    str(closing_event["observed_at"]),
                    final_level=final_level,
                )
            )
            state_changed = True

    if args.dry_run:
        notify_pending(data, dry_run=True)
        return

    if state_changed:
        accounts.save(data)
    if closed_now:
        for closed in closed_now:
            append_journal(closed)
            write_memory(closed)
    sent = notify_pending(data)
    if closed_now or sent:
        accounts.save(data)
    print(
        f"Monitor complete: {milestones_now} target milestone(s), "
        f"{len(closed_now)} closed, {sent} notification(s) sent."
    )


if __name__ == "__main__":
    main()

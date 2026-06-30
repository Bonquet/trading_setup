"""Weekly trade stats from journal/trades.md.

Parses every `### YYYY-MM-DD HH:MM UTC — BUY/SELL @ price` block and computes
stats for a date window (default: last 7 days). Outputs a human-readable
summary to stdout, a JSON blob to data/cache/weekly_stats.json, and (optionally)
appends the summary as a new "Weekly Review" entry to the journal.

Usage:
  python scripts/weekly_stats.py               # last 7 days
  python scripts/weekly_stats.py --days 30     # last 30 days
  python scripts/weekly_stats.py --all         # entire journal
  python scripts/weekly_stats.py --notify      # also send via WhatsApp
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "journal" / "trades.md"
OUT = ROOT / "data" / "cache" / "weekly_stats.json"
# Reply notifier is env-configurable (Telegram workflow sets NOTIFIER_SCRIPT).
NOTIFIER_NAME = os.environ.get("NOTIFIER_SCRIPT", "notify_whatsapp.py")

HEADER_RE = re.compile(
    r"^###\s+(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2})\s*UTC\s+—\s+(?P<dir>BUY|SELL)\s+@\s+(?P<entry>[\d.]+)",
    re.IGNORECASE,
)
FIELD_RE = re.compile(r"^\s*-\s+(?P<k>[A-Za-z][\w /]*?):\s*(?P<v>.+?)\s*$")


def parse_journal(text: str) -> list[dict]:
    trades: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        m = HEADER_RE.match(raw)
        if m:
            if cur:
                trades.append(cur)
            cur = {
                "date": m.group("date"),
                "time": m.group("time"),
                "direction": m.group("dir").upper(),
                "entry": float(m.group("entry")),
                "fields": {},
            }
            continue
        if cur is None:
            continue
        fm = FIELD_RE.match(raw)
        if fm:
            cur["fields"][fm.group("k").strip().lower()] = fm.group("v").strip()
    if cur:
        trades.append(cur)
    return trades


def classify_result(fields: dict) -> str:
    outcome = (fields.get("outcome") or "").lower()
    if "win" in outcome or "tp" in outcome:
        return "win"
    if "loss" in outcome or "sl" in outcome or "stopped" in outcome:
        return "loss"
    if "breakeven" in outcome or outcome.startswith("be"):
        return "breakeven"
    if "missed" in outcome or "invalid" in outcome or "skipped" in outcome:
        return "skipped"
    return "pending"


def extract_r(fields: dict) -> float | None:
    # Look in "r result" or "rr"
    for key in ("r result", "rr", "r"):
        v = fields.get(key)
        if not v:
            continue
        m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*R", v, re.IGNORECASE)
        if m:
            return float(m.group(1))
        try:
            return float(v.rstrip("R").strip())
        except ValueError:
            pass
    return None


def summarize(trades: list[dict], since: datetime | None) -> dict:
    if since:
        trades = [t for t in trades if _parse_dt(t) >= since]
    total = len(trades)
    counts = Counter(classify_result(t["fields"]) for t in trades)
    rs = [r for t in trades if (r := extract_r(t["fields"])) is not None]
    closed = counts["win"] + counts["loss"] + counts["breakeven"]
    win_rate = (counts["win"] / closed * 100) if closed else 0.0
    avg_r = sum(rs) / len(rs) if rs else 0.0
    total_r = sum(rs) if rs else 0.0
    by_strategy = defaultdict(lambda: {"total": 0, "wins": 0, "losses": 0, "r": 0.0})
    for t in trades:
        strat = (t["fields"].get("strategy") or "unknown").split("(")[0].strip()
        by_strategy[strat]["total"] += 1
        cls = classify_result(t["fields"])
        if cls == "win":
            by_strategy[strat]["wins"] += 1
        elif cls == "loss":
            by_strategy[strat]["losses"] += 1
        r = extract_r(t["fields"])
        if r is not None:
            by_strategy[strat]["r"] += r
    return {
        "total_trades": total,
        "closed": closed,
        "wins": counts["win"],
        "losses": counts["loss"],
        "breakeven": counts["breakeven"],
        "pending": counts["pending"],
        "skipped": counts["skipped"],
        "win_rate_pct": round(win_rate, 1),
        "avg_r": round(avg_r, 2),
        "total_r": round(total_r, 2),
        "by_strategy": {k: v for k, v in by_strategy.items()},
        "window_since": since.isoformat() if since else "all-time",
    }


def _parse_dt(trade: dict) -> datetime:
    return datetime.strptime(f"{trade['date']} {trade['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def format_summary(s: dict) -> str:
    header = f"XAU Weekly Review — window: {s['window_since']}"
    body = (
        f"Ideas: {s['total_trades']} | Closed: {s['closed']} | "
        f"Pending: {s['pending']} | Skipped: {s['skipped']}\n"
        f"W/L/BE: {s['wins']}/{s['losses']}/{s['breakeven']}\n"
        f"Win rate: {s['win_rate_pct']}% | Avg R: {s['avg_r']} | Total R: {s['total_r']}"
    )
    strat = ""
    for name, v in s["by_strategy"].items():
        strat += f"\n• {name}: {v['total']} trades, {v['wins']}W/{v['losses']}L, {round(v['r'],2)}R total"
    return f"{header}\n{body}{strat.rstrip()}"


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--days", type=int, default=7, help="days to include (default 7)")
    g.add_argument("--all", action="store_true", help="include all-time trades")
    ap.add_argument("--notify", action="store_true", help="also send via WhatsApp")
    args = ap.parse_args()

    if not JOURNAL.exists():
        print("No journal yet — nothing to review.")
        return
    text = JOURNAL.read_text(encoding="utf-8")
    trades = parse_journal(text)
    since = None if args.all else datetime.now(timezone.utc) - timedelta(days=args.days)
    stats = summarize(trades, since)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2, default=str))

    summary = format_summary(stats)
    print(summary)

    if args.notify:
        print("\n→ Sending via notifier…")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / NOTIFIER_NAME), summary],
            cwd=str(ROOT),
        )


if __name__ == "__main__":
    main()

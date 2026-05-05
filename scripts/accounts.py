"""Multi-account state + P&L for XAU trading.

State file: data/accounts.json (committed, survives CI runs).

Structure:
{
  "active": "main",
  "accounts": {
    "main":    {"balance": 5000.0, "currency": "USD"},
    "savings": {"balance": 10000.0, "currency": "USD"}
  },
  "open":   [ {id, account, direction, entry, sl, tp1, tp2, lots, risk_usd, strategy, opened_at} ],
  "closed": [ {..., exit, pnl_usd, r, status, closed_at} ]
}

Contract (per XAUUSD at standard 100 oz/lot):
  pnl_usd = (exit - entry) * 100 * lots     for BUY
  pnl_usd = (entry - exit) * 100 * lots     for SELL
  r       = pnl_usd / risk_usd

CLI (called from workflow / locally):
  python scripts/accounts.py list
  python scripts/accounts.py set <name> <balance> [currency]   # create or update
  python scripts/accounts.py active <name>
  python scripts/accounts.py open <account> <dir> <entry> <sl> <tp1> <tp2> <strategy> <risk_pct>
  python scripts/accounts.py mirror <account>                   # copy latest open onto another account
  python scripts/accounts.py close <result> [price]             # result = win|loss|be|price ; price optional when result=price
  python scripts/accounts.py pnl
  python scripts/accounts.py parse "<raw whatsapp args>" <command>   # parses "acct1 5000" style args

Most subcommands accept --notify to fire a WhatsApp summary via notify_whatsapp.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "accounts.json"
NOTIFIER = ROOT / "scripts" / "notify_whatsapp.py"
CONTRACT_SIZE = 100.0  # oz per standard lot XAUUSD


# ---------- state I/O ----------

def _empty() -> dict:
    return {"active": None, "accounts": {}, "open": [], "closed": []}


def load() -> dict:
    if not STATE.exists():
        return _empty()
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        for k, default in _empty().items():
            data.setdefault(k, default)
        return data
    except Exception:  # noqa: BLE001
        return _empty()


def save(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------- helpers ----------

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def notify(msg: str) -> None:
    try:
        subprocess.run([sys.executable, str(NOTIFIER), msg], cwd=str(ROOT), check=False)
    except Exception as e:  # noqa: BLE001
        print(f"(notifier failed: {e})")


def pnl_of(direction: str, entry: float, exit_price: float, lots: float) -> float:
    if direction.upper() == "BUY":
        return round((exit_price - entry) * CONTRACT_SIZE * lots, 2)
    return round((entry - exit_price) * CONTRACT_SIZE * lots, 2)


def require_account(data: dict, name: str) -> None:
    if name not in data["accounts"]:
        sys.exit(f"Unknown account: {name}. Known: {', '.join(data['accounts']) or '(none)'}")


def fmt_money(v: float) -> str:
    sign = "+" if v >= 0 else "-"
    return f"{sign}${abs(v):,.2f}"


# ---------- commands ----------

def _dd_status(acc: dict) -> str:
    """Format DD buffer remaining for a prop firm account."""
    max_loss = acc.get("max_loss_usd", 0.0)
    if not max_loss:
        return ""
    initial = acc.get("initial_balance", acc.get("balance", 0))
    used = max(0.0, initial - acc.get("balance", initial))
    remaining = max_loss - used
    pct_used = (used / max_loss * 100) if max_loss else 0
    warn = " [WARN]" if pct_used > 70 else ""
    return f" | DD ${remaining:,.0f}/${max_loss:,.0f} left ({pct_used:.0f}% used){warn}"


def cmd_list() -> str:
    data = load()
    if not data["accounts"]:
        return "No accounts yet. Use /balance <name> <amount> to create one."
    lines = ["Accounts:"]
    for name, acc in data["accounts"].items():
        marker = " (active)" if name == data["active"] else ""
        style = acc.get("style", "intraday")
        cap = acc.get("max_risk_per_trade_usd", 0)
        cap_str = f" | cap ${cap:,.0f}/tr" if cap else ""
        frozen_str = " [FROZEN]" if acc.get("frozen") else ""
        lines.append(f"• {name}: ${acc['balance']:,.2f} [{style}]{cap_str}{_dd_status(acc)}{frozen_str}{marker}")
    # per-account P&L rollup
    pnl_by: dict[str, float] = {k: 0.0 for k in data["accounts"]}
    for t in data["closed"]:
        pnl_by.setdefault(t["account"], 0.0)
        pnl_by[t["account"]] += t.get("pnl_usd", 0.0)
    if any(v != 0 for v in pnl_by.values()):
        lines.append("")
        lines.append("Realized P&L:")
        for name, v in pnl_by.items():
            lines.append(f"• {name}: {fmt_money(v)}")
    opens = len(data["open"])
    if opens:
        lines.append("")
        lines.append(f"Open positions: {opens}")
        for t in data["open"]:
            lines.append(f"  - #{t['id']} {t['account']} {t['direction']} @ {t['entry']} SL {t['sl']} TP {t['tp2']} ({t.get('lots','?')} lots)")
    return "\n".join(lines)


def cmd_set(name: str, balance: float, currency: str = "USD") -> str:
    data = load()
    existing = data["accounts"].get(name) or {}
    new = {
        "balance": float(balance),
        "initial_balance": existing.get("initial_balance", float(balance)),
        "currency": currency,
        "prop_firm": existing.get("prop_firm", False),
        "max_loss_usd": existing.get("max_loss_usd", 0.0),
        "max_risk_per_trade_usd": existing.get("max_risk_per_trade_usd", 0.0),
        "style": existing.get("style", "intraday"),
        "risk_pct": existing.get("risk_pct", 1.0),
    }
    data["accounts"][name] = new
    if data["active"] is None:
        data["active"] = name
    save(data)
    verb = "updated" if existing else "created"
    active = " (now active)" if data["active"] == name and not existing else ""
    return f"Account {verb}: {name} = ${balance:,.2f} {currency} (risk {new['risk_pct']}%, style {new['style']}){active}"


def cmd_buffer(name: str, max_loss: float) -> str:
    data = load()
    require_account(data, name)
    data["accounts"][name]["max_loss_usd"] = float(max_loss)
    data["accounts"][name]["prop_firm"] = max_loss > 0
    save(data)
    return f"DD buffer set: {name} max loss = ${max_loss:,.2f} (prop_firm={'on' if max_loss>0 else 'off'})"


def cmd_maxrisk(name: str, max_risk: float) -> str:
    data = load()
    require_account(data, name)
    data["accounts"][name]["max_risk_per_trade_usd"] = float(max_risk)
    save(data)
    return f"Max risk per trade: {name} = ${max_risk:,.2f}"


def cmd_freeze(name: str, frozen: bool = True) -> str:
    data = load()
    require_account(data, name)
    data["accounts"][name]["frozen"] = frozen
    save(data)
    word = "frozen" if frozen else "unfrozen"
    extra = " — /took, /best signals, mirroring all blocked for this account." if frozen else ""
    return f"Account {name} {word}.{extra}"


def cmd_style(name: str, style: str) -> str:
    data = load()
    require_account(data, name)
    style = style.lower().strip()
    if style not in ("swing", "intraday", "scalp"):
        return f"Unknown style '{style}'. Choose: swing | intraday | scalp"
    data["accounts"][name]["style"] = style
    save(data)
    return f"Style set: {name} = {style}"


def cmd_risk(name: str, pct: float) -> str:
    data = load()
    require_account(data, name)
    if pct <= 0 or pct > 10:
        return f"Risk pct must be between 0 and 10. Got {pct}."
    data["accounts"][name]["risk_pct"] = float(pct)
    save(data)
    return f"Risk set: {name} = {pct}% per trade"


def cmd_active(name: str) -> str:
    data = load()
    require_account(data, name)
    data["active"] = name
    save(data)
    bal = data["accounts"][name]["balance"]
    return f"Active account set to: {name} (${bal:,.2f}). Signals will size against this balance until changed."


def cmd_open(account: str, direction: str, entry: float, sl: float,
             tp1: float, tp2: float, strategy: str, risk_pct: float,
             lots: float | None = None, risk_usd: float | None = None) -> str:
    """Called from run_auto.py when a valid signal fires. Creates an open trade record.
    If lots and risk_usd are provided, uses them directly (preserves engine's prop-cap math).
    Otherwise computes from balance × risk_pct, also clamped by account's max_risk_per_trade_usd.
    """
    data = load()
    require_account(data, account)
    acc = data["accounts"][account]
    if acc.get("frozen"):
        return f"REFUSED: account {account} is frozen. /unfreeze {account} to allow trades."
    bal = acc["balance"]
    cap = acc.get("max_risk_per_trade_usd", 0.0)
    stop_dist = abs(entry - sl)
    if stop_dist <= 0:
        sys.exit("Stop distance must be > 0")

    if lots is not None and risk_usd is not None:
        lots = float(lots)
        risk_usd = float(risk_usd)
    else:
        risk_pct_usd = bal * risk_pct / 100.0
        budget = min(risk_pct_usd, cap) if cap > 0 else risk_pct_usd
        lots = max(0.01, round(budget / (stop_dist * CONTRACT_SIZE), 2))
        risk_usd = round(lots * stop_dist * CONTRACT_SIZE, 2)
    trade_id = now_iso().replace(":", "").replace("-", "")
    trade = {
        "id": trade_id,
        "account": account,
        "direction": direction.upper(),
        "entry": float(entry),
        "sl": float(sl),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "lots": lots,
        "risk_usd": risk_usd,
        "risk_pct": risk_pct,
        "strategy": strategy,
        "opened_at": now_iso(),
    }
    data["open"].append(trade)
    save(data)
    return (f"Opened #{trade_id} on {account}: {direction.upper()} @ {entry} "
            f"SL {sl} TP {tp2} — {lots} lots, risk ${risk_usd:,.2f} ({risk_pct}%)")


def cmd_mirror(dest_account: str, lots_override: float | None = None) -> str:
    """Copy most recent open trade onto another account.
    If lots_override is given, use that exact lot size (broker-imposed sizing);
    otherwise re-size for the destination's balance + risk_pct.
    Refuses if dest account is frozen OR if lot override would exceed the cap by >25%.
    """
    data = load()
    require_account(data, dest_account)
    dest = data["accounts"][dest_account]
    if dest.get("frozen"):
        return f"REFUSED: {dest_account} is frozen. /unfreeze {dest_account} first."
    if not data["open"]:
        return "No open trade to mirror."
    src = data["open"][-1]
    if src["account"] == dest_account:
        return f"Most recent open trade is already on {dest_account}."
    bal = dest["balance"]
    cap = dest.get("max_risk_per_trade_usd", 0.0)
    stop_dist = abs(src["entry"] - src["sl"])
    if lots_override is not None:
        lots = float(lots_override)
        risk_usd = round(lots * stop_dist * CONTRACT_SIZE, 2)
        # Hard guard: refuse if custom lot blows past the prop cap by >25%
        if cap > 0 and risk_usd > cap * 1.25:
            return (f"REFUSED: lot override {lots} on {dest_account} would risk ${risk_usd:.2f}, "
                    f"more than 1.25× cap ${cap:.2f}. Use a smaller lot or /maxrisk {dest_account} <new>.")
        custom_note = " (custom lot)"
    else:
        risk_pct_usd = bal * src["risk_pct"] / 100.0
        budget = min(risk_pct_usd, cap) if cap > 0 else risk_pct_usd
        import math as _m
        lots = max(0.01, _m.floor(budget / (stop_dist * CONTRACT_SIZE) * 100) / 100)
        risk_usd = round(lots * stop_dist * CONTRACT_SIZE, 2)
        custom_note = ""
    trade_id = now_iso().replace(":", "").replace("-", "") + "_m"
    mirror = dict(src)
    mirror.update({
        "id": trade_id,
        "account": dest_account,
        "lots": lots,
        "risk_usd": risk_usd,
        "opened_at": now_iso(),
        "mirrored_from": src["id"],
    })
    data["open"].append(mirror)
    save(data)
    return (f"Mirrored #{src['id']} to {dest_account}{custom_note}: "
            f"{src['direction']} @ {src['entry']} — {lots} lots, risk ${risk_usd:,.2f}")


def cmd_close(result: str, price: float | None = None, reason: str = "") -> str:
    """Close ALL currently-open trades with a shared outcome + optional reason.
    result: win | loss | be | price
    price:  only required when result == 'price'
    reason: free text — recorded with each closed trade
    """
    data = load()
    if not data["open"]:
        return "No open trades to close."

    lines = ["Closed:"]
    total_pnl_by: dict[str, float] = {}
    for trade in list(data["open"]):
        if result == "win":
            exit_p = trade["tp2"]
            status = "win"
        elif result == "loss":
            exit_p = trade["sl"]
            status = "loss"
        elif result == "be":
            exit_p = trade["entry"]
            status = "breakeven"
        elif result == "price":
            if price is None:
                sys.exit("close price required when result=price")
            exit_p = float(price)
            # derive status vs entry direction
            if trade["direction"] == "BUY":
                status = "win" if exit_p > trade["entry"] else ("loss" if exit_p < trade["entry"] else "breakeven")
            else:
                status = "win" if exit_p < trade["entry"] else ("loss" if exit_p > trade["entry"] else "breakeven")
        else:
            sys.exit(f"unknown result: {result}")

        pnl = pnl_of(trade["direction"], trade["entry"], exit_p, trade["lots"])
        r = round(pnl / trade["risk_usd"], 2) if trade["risk_usd"] else 0.0
        closed = dict(trade)
        closed.update({"exit": exit_p, "pnl_usd": pnl, "r": r, "status": status,
                       "closed_at": now_iso(), "reason": reason})
        data["closed"].append(closed)
        data["open"].remove(trade)

        # update account balance
        acc = data["accounts"].get(trade["account"])
        if acc is not None:
            acc["balance"] = round(acc["balance"] + pnl, 2)
        total_pnl_by.setdefault(trade["account"], 0.0)
        total_pnl_by[trade["account"]] += pnl
        why = f" [{reason}]" if reason else ""
        lines.append(f"• #{trade['id']} {trade['account']} {trade['direction']} {status.upper()} @ {exit_p} → {fmt_money(pnl)} ({r}R){why}")

    save(data)
    lines.append("")
    lines.append("New balances:")
    for name, pnl in total_pnl_by.items():
        lines.append(f"• {name}: ${data['accounts'][name]['balance']:,.2f} ({fmt_money(pnl)})")
    return "\n".join(lines)


def _last_spot() -> float | None:
    p = ROOT / "data" / "cache" / "levels.json"
    if not p.exists():
        return None
    try:
        return float(json.loads(p.read_text(encoding="utf-8")).get("spot") or 0) or None
    except Exception:  # noqa: BLE001
        return None


def cmd_current() -> str:
    """Show all currently-open trades with running P&L."""
    data = load()
    if not data["open"]:
        return ("No open trades.\n"
                "Latest cron runs publish signals via /best, /london, /ny — "
                "if a setup fired, you'd see it here.")
    spot = _last_spot()
    lines = [f"Open trades ({len(data['open'])}):"]
    if spot:
        lines.append(f"Last cached spot: ${spot}")
    lines.append("")
    for t in data["open"]:
        line = (f"#{t['id']} [{t['account']}] {t['direction']} @ {t['entry']}\n"
                f"  SL {t['sl']} | TP {t['tp2']} | {t['lots']} lots | risk ${t['risk_usd']:,.2f}")
        if spot:
            running = pnl_of(t["direction"], t["entry"], spot, t["lots"])
            r = round(running / t["risk_usd"], 2) if t["risk_usd"] else 0.0
            line += f"\n  Running: {fmt_money(running)} ({r}R) at spot ${spot}"
        line += f"\n  Strategy: {t.get('strategy','?')} | opened {t.get('opened_at','?')}"
        lines.append(line)
    return "\n".join(lines)


def cmd_pnl() -> str:
    data = load()
    if not data["accounts"]:
        return "No accounts yet."
    lines = ["P&L report:"]
    total = 0.0
    for name, acc in data["accounts"].items():
        closed = [t for t in data["closed"] if t["account"] == name]
        pnl = round(sum(t.get("pnl_usd", 0) for t in closed), 2)
        wins = sum(1 for t in closed if t.get("status") == "win")
        losses = sum(1 for t in closed if t.get("status") == "loss")
        be = sum(1 for t in closed if t.get("status") == "breakeven")
        total += pnl
        lines.append(f"• {name}: {fmt_money(pnl)} ({wins}W/{losses}L/{be}BE, {len(closed)} closed) → ${acc['balance']:,.2f}{_dd_status(acc)}")
    lines.append("")
    lines.append(f"Total realized: {fmt_money(total)}")
    if data["open"]:
        lines.append(f"Open: {len(data['open'])} position(s)")
    return "\n".join(lines)


# ---------- WhatsApp args parser ----------
# Handles messy user input like "acct1 5000", "acct1 5000 USD", "main 5,000", "main $5000"
def parse_tokens(raw: str) -> list[str]:
    cleaned = raw.replace(",", "").replace("$", "").strip()
    return [t for t in cleaned.split() if t]


def handle_whatsapp(command: str, raw_args: str, with_notify: bool = True) -> None:
    """Dispatcher for inbound WhatsApp slash commands (called by workflow)."""
    cmd = command.lower().lstrip("/")
    toks = parse_tokens(raw_args)
    try:
        if cmd == "accounts":
            out = cmd_list()
        elif cmd == "balance":
            if len(toks) < 2:
                out = "Usage: /balance <name> <amount> [currency]\nExample: /balance main 5000"
            else:
                name, amt, *rest = toks
                currency = rest[0].upper() if rest else "USD"
                out = cmd_set(name, float(amt), currency)
        elif cmd == "active":
            if not toks:
                out = "Usage: /active <name>"
            else:
                out = cmd_active(toks[0])
        elif cmd == "took":
            if not toks:
                out = ("Usage: /took <account> [lots]\n"
                       "Mirrors the most recent open trade onto that account.\n"
                       "Optional 2nd arg sets exact lot size (otherwise re-sized to that account's balance × risk%).")
            else:
                lots = None
                if len(toks) >= 2:
                    try:
                        lots = float(toks[1])
                    except ValueError:
                        lots = None
                out = cmd_mirror(toks[0], lots_override=lots)
        elif cmd == "close":
            if not toks:
                out = ("Usage: /close <result> [reason words...]\n"
                       "result: win | loss | be | <price>\n"
                       "Optional reason is recorded with the closed trade.\n"
                       "Examples:\n"
                       "  /close win clean run to TP\n"
                       "  /close loss news spike past stop\n"
                       "  /close 4720.5 trail-stop hit")
            else:
                first = toks[0].lower().lstrip("@")
                rest_reason = " ".join(toks[1:]).strip()
                if first in ("win", "loss", "be"):
                    out = cmd_close(first, reason=rest_reason)
                else:
                    try:
                        out = cmd_close("price", float(first), reason=rest_reason)
                    except ValueError:
                        out = f"Unrecognised close argument: {toks[0]}. Use win/loss/be or a price."
        elif cmd == "pnl":
            out = cmd_pnl()
        elif cmd == "current":
            out = cmd_current()
        elif cmd == "risk":
            if len(toks) < 2:
                out = "Usage: /risk <account> <pct>\nExample: /risk main 2  (sets 2% risk per trade)"
            else:
                try:
                    out = cmd_risk(toks[0], float(toks[1]))
                except ValueError:
                    out = f"Bad pct value: {toks[1]}"
        elif cmd == "buffer":
            if len(toks) < 2:
                out = "Usage: /buffer <account> <max_loss_usd>\nExample: /buffer main 200  (FTMO $5k = $200 daily DD)"
            else:
                out = cmd_buffer(toks[0], float(toks[1]))
        elif cmd == "maxrisk":
            if len(toks) < 2:
                out = "Usage: /maxrisk <account> <usd>\nExample: /maxrisk main 20  (cap risk at $20/trade)"
            else:
                out = cmd_maxrisk(toks[0], float(toks[1]))
        elif cmd == "style":
            if len(toks) < 2:
                out = "Usage: /style <account> <swing|intraday|scalp>\nExample: /style main intraday"
            else:
                out = cmd_style(toks[0], toks[1])
        elif cmd == "freeze":
            if not toks:
                out = "Usage: /freeze <account>\nBlocks new trades, mirrors, and signals on this account until /unfreeze."
            else:
                out = cmd_freeze(toks[0], frozen=True)
        elif cmd == "unfreeze":
            if not toks:
                out = "Usage: /unfreeze <account>"
            else:
                out = cmd_freeze(toks[0], frozen=False)
        else:
            out = f"Unknown account command: /{cmd}"
    except SystemExit as e:
        out = f"Error: {e}"

    print(out)
    if with_notify:
        notify(out)


# ---------- CLI dispatch ----------

def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("See docstring: python scripts/accounts.py {list|set|active|open|mirror|close|pnl|whatsapp}")
        return
    sub = args[0]
    rest = args[1:]
    # Shared --notify flag
    do_notify = "--notify" in rest
    rest = [r for r in rest if r != "--notify"]

    if sub == "whatsapp":
        # whatsapp <command> <raw_args_string>
        if len(rest) < 1:
            sys.exit("Usage: whatsapp <command> [raw_args...]")
        command = rest[0]
        raw = " ".join(rest[1:]) if len(rest) > 1 else ""
        handle_whatsapp(command, raw, with_notify=True)
        return

    if sub == "list":
        out = cmd_list()
    elif sub == "set":
        if len(rest) < 2:
            sys.exit("Usage: set <name> <balance> [currency]")
        out = cmd_set(rest[0], float(rest[1]), rest[2] if len(rest) > 2 else "USD")
    elif sub == "active":
        out = cmd_active(rest[0])
    elif sub == "open":
        if len(rest) < 8:
            sys.exit("Usage: open <account> <dir> <entry> <sl> <tp1> <tp2> <strategy> <risk_pct> [<lots> <risk_usd>]")
        lots_arg = float(rest[8]) if len(rest) > 8 else None
        risk_usd_arg = float(rest[9]) if len(rest) > 9 else None
        out = cmd_open(rest[0], rest[1], float(rest[2]), float(rest[3]),
                       float(rest[4]), float(rest[5]), rest[6], float(rest[7]),
                       lots=lots_arg, risk_usd=risk_usd_arg)
    elif sub == "mirror":
        lots = float(rest[1]) if len(rest) > 1 else None
        out = cmd_mirror(rest[0], lots_override=lots)
    elif sub == "close":
        res = rest[0]
        price = float(rest[1]) if (len(rest) > 1 and res == "price") else None
        reason = " ".join(rest[2:]) if (len(rest) > 2 and res == "price") else " ".join(rest[1:])
        out = cmd_close(res, price, reason=reason)
    elif sub == "pnl":
        out = cmd_pnl()
    elif sub == "current":
        out = cmd_current()
    elif sub == "risk":
        out = cmd_risk(rest[0], float(rest[1]))
    elif sub == "freeze":
        out = cmd_freeze(rest[0], frozen=True)
    elif sub == "unfreeze":
        out = cmd_freeze(rest[0], frozen=False)
    elif sub == "buffer":
        out = cmd_buffer(rest[0], float(rest[1]))
    elif sub == "maxrisk":
        out = cmd_maxrisk(rest[0], float(rest[1]))
    elif sub == "style":
        out = cmd_style(rest[0], rest[1])
    else:
        sys.exit(f"unknown subcommand: {sub}")

    print(out)
    if do_notify:
        notify(out)


if __name__ == "__main__":
    main()

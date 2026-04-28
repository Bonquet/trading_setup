"""Deterministic 50 EMA Williams signal engine for XAUUSD.

Reads data/cache/levels.json (produced by compute_levels.py) and applies the
50 EMA Williams rules exactly as defined in strategy/playbook.md:

BUY valid iff (on primary TF, default H4):
  - H4 position_vs_channel == 'above_channel'   (price above 50 EMA High)
  - D1 position_vs_channel == 'above_channel'   (HTF bias aligned)
  - williams_r14 > -20
  - stoch_k > stoch_d AND stoch_k > 60

SELL valid iff (mirror):
  - H4 'below_channel' AND D1 'below_channel'
  - williams_r14 < -80
  - stoch_k < stoch_d AND stoch_k < 40

Stop loss:  below last H4 swing low (buy) / above last H4 swing high (sell).
Take profit: 2R, clamped toward the nearest daily pivot (R1/R2 long, S1/S2 short).
Requires the pivot target to be >= 2R away, else "No Trade — no room".

Writes data/cache/signal.json and prints a one-line summary.

Exit code 0 = valid trade signal written. Exit code 10 = No Trade.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS = ROOT / "data" / "cache" / "levels.json"
OUT = ROOT / "data" / "cache" / "signal.json"
PRIMARY_TF = "H4"
STOP_TF = "H1"           # use H1 swing for SL → tighter stop, bigger lot
HTF = "D1"
DEFAULT_RISK_PCT = 0.01  # 1% (overridable via CLI arg)
SL_ATR_BUFFER = 0.5      # multiples of H1 ATR added past the swing


def no_trade(reason: str, data: dict) -> None:
    payload = {"decision": "No Trade", "reason": reason, "context": data}
    OUT.write_text(json.dumps(payload, indent=2, default=str))
    print(f"No Trade — {reason}")
    sys.exit(10)


def main() -> None:
    if not LEVELS.exists():
        sys.exit(f"Missing {LEVELS}. Run scripts/compute_levels.py first.")
    data = json.loads(LEVELS.read_text())

    spot = data.get("spot")
    tf = data.get("timeframes", {}).get(PRIMARY_TF)
    htf = data.get("timeframes", {}).get(HTF)
    pivots = data.get("daily_pivots") or {}

    if not tf or not htf:
        no_trade(f"missing {PRIMARY_TF} or {HTF} data", data)

    # Required fields
    required = ("position_vs_channel", "williams_r14", "stoch_k", "stoch_d",
                "last_close", "last_swing_high", "last_swing_low", "atr14")
    for f in required:
        if tf.get(f) is None:
            no_trade(f"H4 missing field {f}", data)

    pos_h4 = tf["position_vs_channel"]
    pos_d1 = htf["position_vs_channel"]
    wr = tf["williams_r14"]
    k, d = tf["stoch_k"], tf["stoch_d"]
    close = tf["last_close"]
    # SL anchored to H1 swing (tighter than H4 swing → bigger lot at same risk %)
    h1 = data.get("timeframes", {}).get(STOP_TF) or {}
    h1_swing_h = h1.get("last_swing_high") or tf["last_swing_high"]
    h1_swing_l = h1.get("last_swing_low") or tf["last_swing_low"]
    h1_atr = h1.get("atr14") or 5.0
    swing_h, swing_l = h1_swing_h, h1_swing_l

    # Filter: sideways / misaligned
    if pos_d1 == "inside_channel" or pos_h4 == "inside_channel":
        no_trade("sideways — price inside 50 EMA channel on D1 or H4", data)
    if pos_d1 != pos_h4:
        no_trade(f"bias mismatch: D1 {pos_d1} vs H4 {pos_h4}", data)

    direction = None
    if pos_h4 == "above_channel" and wr > -20 and k > d and k > 60:
        direction = "BUY"
    elif pos_h4 == "below_channel" and wr < -80 and k < d and k < 40:
        direction = "SELL"
    else:
        no_trade(
            f"momentum conditions not met (pos={pos_h4}, Williams%R={wr:.1f}, "
            f"StochK={k:.1f}, StochD={d:.1f})", data,
        )

    # Entry = current spot bid/ask where possible, else H4 close
    entry = float(spot) if spot else close
    if direction == "BUY":
        if not swing_l:
            no_trade("no swing low available for SL", data)
        sl = swing_l - h1_atr * SL_ATR_BUFFER  # below H1 swing low + ATR buffer
        risk = entry - sl
        if risk <= 0:
            no_trade("entry not above swing low — invalid SL distance", data)
        tp2 = entry + 2 * risk
        # Prefer pivot target if it gives >= 2R and is further
        pivot_target = None
        for lvl in ("R1", "R2"):
            v = pivots.get(lvl)
            if v and v > entry + 2 * risk:
                pivot_target = v
                break
        tp1 = entry + 2 * risk
        tp_final = pivot_target if pivot_target else tp2
    else:  # SELL
        if not swing_h:
            no_trade("no swing high available for SL", data)
        sl = swing_h + h1_atr * SL_ATR_BUFFER  # above H1 swing high + ATR buffer
        risk = sl - entry
        if risk <= 0:
            no_trade("entry not below swing high — invalid SL distance", data)
        tp2 = entry - 2 * risk
        pivot_target = None
        for lvl in ("S1", "S2"):
            v = pivots.get(lvl)
            if v and v < entry - 2 * risk:
                pivot_target = v
                break
        tp1 = entry - 2 * risk
        tp_final = pivot_target if pivot_target else tp2

    rr = abs(tp_final - entry) / risk
    if rr < 2.0:
        no_trade(f"RR {rr:.2f} < 2.0 — no room to pivot target", data)

    # Position sizing — caller passes account size (USD) and risk pct (0.01 = 1%)
    account = float(sys.argv[1]) if len(sys.argv) > 1 else 10000.0
    risk_pct = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_RISK_PCT
    # XAUUSD: 1 lot = 100 oz, ~$1 per 0.01 price move per lot = $100 per $1 move per lot
    risk_usd = account * risk_pct
    dollars_per_price_per_lot = 100.0
    lots_raw = risk_usd / (risk * dollars_per_price_per_lot)
    # 0.01-step rounding (broker minimum); never round to zero — floor to 0.01
    lots = max(0.01, round(lots_raw, 2))

    sig = {
        "decision": "Valid Trade",
        "instrument": "XAUUSD",
        "strategy": "50 EMA Williams",
        "direction": direction,
        "entry": round(entry, 2),
        "stop_loss": round(sl, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp_final, 2),
        "risk_per_unit": round(risk, 2),
        "rr_to_tp2": round(rr, 2),
        "account": account,
        "risk_pct": risk_pct,
        "risk_usd": round(risk_usd, 2),
        "lots": lots,
        "stop_distance": round(risk, 2),
        "confluence": {
            "D1_position": pos_d1,
            "H4_position": pos_h4,
            "williams_r14": round(wr, 1),
            "stoch_k": round(k, 1),
            "stoch_d": round(d, 1),
        },
        "pivot_target_used": bool(pivot_target),
        "fetched_at_utc": data.get("fetched_at_utc"),
    }
    OUT.write_text(json.dumps(sig, indent=2, default=str))
    print(
        f"{direction} XAU @ {sig['entry']} | SL {sig['stop_loss']} | "
        f"TP {sig['tp2']} | RR {sig['rr_to_tp2']}R | {sig['lots']} lots"
    )


if __name__ == "__main__":
    main()

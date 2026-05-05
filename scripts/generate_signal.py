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
DEFAULT_RISK_PCT = 0.01  # 1% (overridable via CLI arg)

# Style → (PRIMARY_TF, HTF_BIAS, STOP_TF, SL_ATR_BUFFER)
# - swing: H4 setup, D1 bias, H1 stop          (50-100pt stops, 1-3 day holds)
# - intraday: H1 setup, H4 bias, M15 stop      (15-30pt stops, 1-6h holds; prop-firm friendly)
# - scalp: M15 setup, H1 bias, M15 ATR stop    (5-15pt stops, <1h holds; very twitchy)
STYLES = {
    "swing":    {"primary": "H4",  "htf": "D1", "stop_tf": "H1",  "atr_buf": 0.5,  "wr_long": -20,  "wr_short": -80, "stoch_long": 60,  "stoch_short": 40},
    "intraday": {"primary": "H1",  "htf": "H4", "stop_tf": "M15", "atr_buf": 0.75, "wr_long": -25,  "wr_short": -75, "stoch_long": 55,  "stoch_short": 45},
    "scalp":    {"primary": "M15", "htf": "H1", "stop_tf": "M15", "atr_buf": 1.5,  "wr_long": -30,  "wr_short": -70, "stoch_long": 50,  "stoch_short": 50},
}
DEFAULT_STYLE = "swing"


def no_trade(reason: str, data: dict) -> None:
    payload = {"decision": "No Trade", "reason": reason, "context": data}
    OUT.write_text(json.dumps(payload, indent=2, default=str))
    print(f"No Trade — {reason}")
    sys.exit(10)


def main() -> None:
    if not LEVELS.exists():
        sys.exit(f"Missing {LEVELS}. Run scripts/compute_levels.py first.")
    data = json.loads(LEVELS.read_text())

    # Style flag (--style=intraday|swing|scalp). Default: intraday.
    style = DEFAULT_STYLE
    for arg in sys.argv:
        if arg.startswith("--style="):
            style = arg.split("=", 1)[1].lower()
    if style not in STYLES:
        sys.exit(f"Unknown style '{style}'. Choose: {', '.join(STYLES)}")
    cfg = STYLES[style]
    PRIMARY_TF = cfg["primary"]
    HTF = cfg["htf"]
    STOP_TF = cfg["stop_tf"]
    SL_ATR_BUFFER = cfg["atr_buf"]

    spot = data.get("spot")
    tf = data.get("timeframes", {}).get(PRIMARY_TF)
    htf = data.get("timeframes", {}).get(HTF)
    pivots = data.get("daily_pivots") or {}

    if not tf or not htf:
        no_trade(f"missing {PRIMARY_TF} or {HTF} data", data)

    # Required fields on primary TF
    required = ("position_vs_channel", "williams_r14", "stoch_k", "stoch_d",
                "last_close", "last_swing_high", "last_swing_low", "atr14")
    for f in required:
        if tf.get(f) is None:
            no_trade(f"{PRIMARY_TF} missing field {f}", data)

    pos_p = tf["position_vs_channel"]      # primary TF position
    pos_b = htf["position_vs_channel"]     # bias TF position
    wr = tf["williams_r14"]
    k, d = tf["stoch_k"], tf["stoch_d"]
    close = tf["last_close"]
    # SL anchored to STOP_TF swing
    stop_data = data.get("timeframes", {}).get(STOP_TF) or {}
    stop_swing_h = stop_data.get("last_swing_high") or tf["last_swing_high"]
    stop_swing_l = stop_data.get("last_swing_low") or tf["last_swing_low"]
    stop_atr = stop_data.get("atr14") or 5.0
    swing_h, swing_l = stop_swing_h, stop_swing_l

    # Filter: sideways / misaligned (using primary + bias)
    if pos_b == "inside_channel" or pos_p == "inside_channel":
        no_trade(f"sideways — price inside 50 EMA channel on {HTF} or {PRIMARY_TF}", data)
    if pos_b != pos_p:
        no_trade(f"bias mismatch: {HTF} {pos_b} vs {PRIMARY_TF} {pos_p}", data)

    direction = None
    if pos_p == "above_channel" and wr > cfg["wr_long"] and k > d and k > cfg["stoch_long"]:
        direction = "BUY"
    elif pos_p == "below_channel" and wr < cfg["wr_short"] and k < d and k < cfg["stoch_short"]:
        direction = "SELL"
    else:
        no_trade(
            f"momentum conditions not met on {PRIMARY_TF} (pos={pos_p}, Williams%R={wr:.1f}, "
            f"StochK={k:.1f}, StochD={d:.1f}; thresholds wr_long>{cfg['wr_long']} k>{cfg['stoch_long']} "
            f"or wr_short<{cfg['wr_short']} k<{cfg['stoch_short']})", data,
        )

    # Entry = current spot bid/ask where possible, else H4 close
    entry = float(spot) if spot else close

    # H4 ATR is used for the volatility-based stop floor on swing trades
    primary_atr = tf.get("atr14") or stop_atr or 5.0

    # SL placement — pick the TIGHTEST valid stop from candidates so the lot can grow.
    # Candidates:
    #   A) structure stop = STOP_TF swing ± buffer × STOP_TF ATR
    #   B) volatility stop = 1.5 × PRIMARY_TF ATR
    # Floor: never tighter than 1.0 × PRIMARY_TF ATR (avoids noise stop-outs).
    # Choose min(A, B) but >= floor.
    atr_stop_dist = 1.5 * primary_atr
    atr_floor = 1.0 * primary_atr

    if direction == "BUY":
        if not swing_l:
            no_trade("no swing low available for SL", data)
        struct_dist = entry - (swing_l - stop_atr * SL_ATR_BUFFER)
        # Pick the tighter, but not below ATR floor
        risk = max(min(struct_dist, atr_stop_dist), atr_floor)
        sl = entry - risk
        if risk <= 0:
            no_trade("invalid SL distance", data)
        # TP search: take the FURTHEST pivot still inside reason (≤ 4R), giving 2.5–4R targets
        tp_2r = entry + 2 * risk
        tp_25r = entry + 2.5 * risk
        tp_max = entry + 4 * risk
        pivot_target = None
        for lvl in ("R2", "R1"):  # try R2 first (further target)
            v = pivots.get(lvl)
            if v and tp_25r <= v <= tp_max:
                pivot_target = v
                break
        tp_final = pivot_target if pivot_target else tp_25r
        tp1 = tp_2r
    else:  # SELL
        if not swing_h:
            no_trade("no swing high available for SL", data)
        struct_dist = (swing_h + stop_atr * SL_ATR_BUFFER) - entry
        risk = max(min(struct_dist, atr_stop_dist), atr_floor)
        sl = entry + risk
        if risk <= 0:
            no_trade("invalid SL distance", data)
        tp_2r = entry - 2 * risk
        tp_25r = entry - 2.5 * risk
        tp_max = entry - 4 * risk
        pivot_target = None
        for lvl in ("S2", "S1"):
            v = pivots.get(lvl)
            if v and tp_max <= v <= tp_25r:
                pivot_target = v
                break
        tp_final = pivot_target if pivot_target else tp_25r
        tp1 = tp_2r

    rr = abs(tp_final - entry) / risk
    if rr < 2.0:
        no_trade(f"RR {rr:.2f} < 2.0 — no room to target", data)

    # Position sizing — caller passes account size, risk pct, and (optional) dollar cap
    account = float(sys.argv[1]) if len(sys.argv) > 1 else 10000.0
    risk_pct = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_RISK_PCT
    # max_risk_usd is a hard $-cap (prop firm DD-buffer aware). 0 means "no cap, use risk_pct only".
    max_risk_usd = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    risk_pct_usd = account * risk_pct
    if max_risk_usd > 0:
        budget_usd = min(risk_pct_usd, max_risk_usd)
        cap_source = "prop $-cap" if max_risk_usd <= risk_pct_usd else f"{risk_pct*100:.1f}% of balance"
    else:
        budget_usd = risk_pct_usd
        cap_source = f"{risk_pct*100:.1f}% of balance"

    # XAUUSD: 1 lot = 100 oz, $100 per $1 price move per standard lot.
    dollars_per_price_per_lot = 100.0
    lots_raw = budget_usd / (risk * dollars_per_price_per_lot)
    # Floor to 0.01 lots so we NEVER overshoot the budget (round-up would risk more)
    import math
    lots = math.floor(lots_raw * 100) / 100.0
    # Broker minimum is 0.01 lot. If even minimum exceeds the budget, refuse the trade
    # (this is the prop-firm safety net — wide stop = no trade).
    if lots < 0.01:
        actual_min_risk = 0.01 * risk * dollars_per_price_per_lot
        no_trade(
            f"stop too wide for risk budget ({cap_source} = ${budget_usd:.2f}); "
            f"minimum 0.01 lot would risk ${actual_min_risk:.2f} on {risk:.1f}-pt stop. "
            f"Skip this setup — wait for a tighter structure.", data,
        )
    # Floor to 0.01; flag (don't refuse) if 0.01 lot exceeds the prop cap.
    # User sees the signal + warning and decides whether to take.
    if lots < 0.01:
        lots = 0.01
    risk_usd = lots * risk * dollars_per_price_per_lot
    cap_exceeded = max_risk_usd > 0 and risk_usd > max_risk_usd
    cap_exceeded_pct = round((risk_usd / max_risk_usd * 100), 0) if max_risk_usd > 0 else 0
    # Only hard-refuse if WILDLY beyond cap (3×) — that level of overshoot is structurally unsafe.
    if max_risk_usd > 0 and risk_usd > max_risk_usd * 3:
        no_trade(
            f"min lot risks ${risk_usd:.2f} > 3× cap ${max_risk_usd:.2f} "
            f"on {risk:.1f}-pt stop ({style}). Truly unsafe — wait for tighter structure.", data,
        )

    sig = {
        "decision": "Valid Trade",
        "instrument": "XAUUSD",
        "style": style,
        "primary_tf": PRIMARY_TF,
        "bias_tf": HTF,
        "stop_tf": STOP_TF,
        "strategy": f"50 EMA Williams ({style})",
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
        "max_risk_cap_usd": max_risk_usd,
        "cap_source": cap_source,
        "cap_exceeded": cap_exceeded,
        "cap_exceeded_pct": cap_exceeded_pct,
        "lots": lots,
        "stop_distance": round(risk, 2),
        "confluence": {
            f"{HTF}_position": pos_b,
            f"{PRIMARY_TF}_position": pos_p,
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

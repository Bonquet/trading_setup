"""
Inverted Fair Value Gap (IFVG) — momentum-shift scalp.

1. Detect a 3-candle FVG (bullish: low[k] > high[k-2]; bearish: high[k] < low[k-2]).
2. INVERSION: price closes completely through the gap with a full body
   (bull FVG -> close below its bottom = now resistance; bear FVG -> close above
   its top = now support).
3. ENTRY: on the pullback to the inverted gap's boundary, trade the bounce.
   Stop beyond the far side of the gap; target a small fixed move.
Tests several target sizes + killzone on/off, with realistic costs.
"""
from __future__ import annotations
import numpy as np, pandas as pd
import data_loader, indicators as ind
from engine import Trade, BacktestResult, COST_SCENARIOS, USD_PER_LOT_PER_DOLLAR
import metrics as M


def run_ifvg(tf="15m", tp_usd=10.0, buf=0.2, valid_bars=4, fvg_life=20,
             risk=0.01, start=10_000.0, cost_name="realistic", max_bars=20,
             use_kz=True, min_gap=0.0, fixed_lot=0.0):
    df = data_loader.load(tf)
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    hour = df.index.hour.values
    n = len(df)
    cost = COST_SCENARIOS[cost_name]

    def in_kz(i):
        return True if not use_kz else ((7 <= hour[i] <= 10) or (12 <= hour[i] <= 15))

    equity = start
    eq = np.full(n, np.nan)
    trades = []
    pos = None
    pend = None
    fvgs = []  # active FVGs: dict(lo, hi, type, born)

    for i in range(3, n):
        # ---- manage open position ----
        if pos is not None:
            ep = None; reason = ""
            if pos.direction == 1:
                if l[i] <= pos.stop: ep, reason = pos.stop, "stop"
                elif h[i] >= pos.target: ep, reason = pos.target, "target"
            else:
                if h[i] >= pos.stop: ep, reason = pos.stop, "stop"
                elif l[i] <= pos.target: ep, reason = pos.target, "target"
            if ep is None and pos.bars_held >= max_bars:
                ep, reason = o[i], "time"
            if ep is not None:
                gross = (ep - pos.entry) * pos.direction * pos.lots * USD_PER_LOT_PER_DOLLAR
                fees = cost.spread * pos.lots * USD_PER_LOT_PER_DOLLAR + cost.commission_per_lot * pos.lots
                pnl = gross - fees
                rd = abs(pos.entry - pos.stop) * pos.lots * USD_PER_LOT_PER_DOLLAR
                pos.exit_time = df.index[i]; pos.exit = ep; pos.pnl = pnl
                pos.r_multiple = pnl / rd if rd > 0 else 0; pos.reason = reason
                equity += pnl; trades.append(pos); pos = None
            else:
                pos.bars_held += 1

        # ---- pending limit fill (pullback to inverted boundary) ----
        if pos is None and pend is not None:
            if i > pend["expiry"]:
                pend = None
            else:
                fill = None
                if pend["dir"] == 1 and l[i] <= pend["limit"]:
                    fill = pend["limit"] if o[i] >= pend["limit"] else o[i]
                elif pend["dir"] == -1 and h[i] >= pend["limit"]:
                    fill = pend["limit"] if o[i] <= pend["limit"] else o[i]
                if fill is not None:
                    sd = abs(fill - pend["stop"])
                    if sd > 0:
                        if fixed_lot > 0:
                            lots = fixed_lot
                        else:
                            lots = max(0.01, np.floor((equity * risk / (sd * USD_PER_LOT_PER_DOLLAR)) / 0.01) * 0.01)
                        tgt = fill + pend["dir"] * tp_usd
                        pos = Trade(pend["dir"], df.index[i], fill, pend["stop"], tgt, lots, conf=1)
                    pend = None

        # ---- register a new FVG formed at bar i (gap between i-2 and i) ----
        if l[i] > h[i - 2] and (l[i] - h[i - 2]) >= min_gap:
            fvgs.append({"lo": h[i - 2], "hi": l[i], "type": "bull", "born": i})
        elif h[i] < l[i - 2] and (l[i - 2] - h[i]) >= min_gap:
            fvgs.append({"lo": h[i], "hi": l[i - 2], "type": "bear", "born": i})
        # prune old
        fvgs = [g for g in fvgs if i - g["born"] <= fvg_life]

        # ---- check inversion on this close, arm a pullback limit ----
        if pos is None and pend is None and in_kz(i):
            for g in list(fvgs):
                if g["type"] == "bull" and c[i] < g["lo"]:
                    # bull FVG inverted -> resistance -> SHORT the pullback to lo
                    pend = {"dir": -1, "limit": g["lo"], "stop": g["hi"] + buf, "expiry": i + valid_bars}
                    fvgs.remove(g); break
                elif g["type"] == "bear" and c[i] > g["hi"]:
                    # bear FVG inverted -> support -> LONG the pullback to hi
                    pend = {"dir": 1, "limit": g["hi"], "stop": g["lo"] - buf, "expiry": i + valid_bars}
                    fvgs.remove(g); break

        eq[i] = equity

    res = BacktestResult(trades=trades, equity_curve=pd.Series(eq, index=df.index).ffill(),
                         start_equity=start, end_equity=equity, cost=cost_name)
    return res


if __name__ == "__main__":
    print("IFVG momentum-shift scalp — target sweep, killzone on/off (realistic costs)\n")
    print(f'{"tf / TP / KZ":>20} | trades | t/yr | win% | PF | expR | ret% | DD%')
    for tf in ["15m", "1h"]:
        for kz in [True, False]:
            for tp in [3.0, 6.0, 10.0, 15.0]:
                res = run_ifvg(tf, tp_usd=tp, use_kz=kz)
                m = M.compute(res, tf)
                yrs = (res.equity_curve.index[-1] - res.equity_curve.index[0]).days / 365.25
                kzs = "KZ" if kz else "all"
                print(f'{tf} TP${tp:>4.0f} {kzs:>3} | {m["trades"]:>6} | {m["trades"]/yrs:>4.0f} | {m["win_rate"]:>4} | {m["profit_factor"]:>4} | {m["expectancy_R"]:>6} | {m["total_return_pct"]:>7} | {m["max_dd_pct"]:>6}')
        print()

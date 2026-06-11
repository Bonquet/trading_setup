"""
fvg_backtest.py — SMC "sniper entry" (Trading Strategy Guides Lecture 13).

HTF bias -> on the entry timeframe, find a Fair Value Gap (3-bar imbalance) in the
trend direction, place a LIMIT order into the gap (enter on the retracement, not
chasing), tight stop just beyond the gap, target a large R multiple (HTF move).

This adds LIMIT-order fills (the core of the method) which the main engine lacks.
"""
from __future__ import annotations
import numpy as np, pandas as pd
import data_loader, indicators as ind
from engine import Trade, BacktestResult, COST_SCENARIOS, USD_PER_LOT_PER_DOLLAR
import metrics as M

BIAS_HOURS = {"4h": 4, "1d": 24, "1h": 1}


def run_fvg(entry_tf="15m", bias_tf="4h", rr=3.0, valid_bars=10, atr_buf=0.2,
            risk=0.01, start=10_000.0, cost_name="realistic",
            min_gap_atr=0.25, max_bars=80, require_structure=True):
    df = data_loader.load(entry_tf)
    bias = ind.htf_bias_aligned(df.index, data_loader.load(bias_tf), BIAS_HOURS[bias_tf])
    ms = ind.market_structure(df, 2, 2)
    trend = ms["trend"]
    atr = ind.atr(df, 14).values
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    n = len(df)
    cost = COST_SCENARIOS[cost_name]

    equity = start
    eq = np.full(n, np.nan)
    trades = []
    pos = None
    pend = None  # pending limit order

    for i in range(2, n):
        # ---- manage open position (stop priority) ----
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
                risk_d = abs(pos.entry - pos.stop) * pos.lots * USD_PER_LOT_PER_DOLLAR
                pos.exit_time = df.index[i]; pos.exit = ep; pos.pnl = pnl
                pos.r_multiple = pnl / risk_d if risk_d > 0 else 0
                pos.reason = reason
                equity += pnl; trades.append(pos); pos = None
            else:
                pos.bars_held += 1

        # ---- check pending limit fill ----
        if pos is None and pend is not None:
            if i > pend["expiry"]:
                pend = None
            else:
                filled = False; fill = None
                if pend["dir"] == 1 and l[i] <= pend["limit"]:
                    fill = min(pend["limit"], o[i]) if o[i] < pend["limit"] else pend["limit"]; filled = True
                elif pend["dir"] == -1 and h[i] >= pend["limit"]:
                    fill = max(pend["limit"], o[i]) if o[i] > pend["limit"] else pend["limit"]; filled = True
                if filled:
                    sd = abs(fill - pend["stop"])
                    if sd > 0:
                        lots = max(0.01, np.floor((equity * risk / (sd * USD_PER_LOT_PER_DOLLAR)) / 0.01) * 0.01)
                        tgt = fill + pend["dir"] * rr * sd
                        pos = Trade(direction=pend["dir"], entry_time=df.index[i], entry=fill,
                                    stop=pend["stop"], target=tgt, lots=lots, conf=1)
                    pend = None

        # ---- detect new FVG and arm a limit (if flat & nothing pending) ----
        if pos is None and pend is None:
            okbull = (bias[i] == 1) and (not require_structure or trend[i] == 1)
            okbear = (bias[i] == -1) and (not require_structure or trend[i] == -1)
            # bullish FVG: gap between high[i-2] and low[i]
            if okbull and l[i] > h[i - 2] and (l[i] - h[i - 2]) >= min_gap_atr * atr[i]:
                gl, gh = h[i - 2], l[i]
                limit = (gl + gh) / 2
                stop = gl - atr_buf * atr[i]
                pend = {"dir": 1, "limit": limit, "stop": stop, "expiry": i + valid_bars}
            elif okbear and h[i] < l[i - 2] and (l[i - 2] - h[i]) >= min_gap_atr * atr[i]:
                gh, gl = l[i - 2], h[i]
                limit = (gl + gh) / 2
                stop = gh + atr_buf * atr[i]
                pend = {"dir": -1, "limit": limit, "stop": stop, "expiry": i + valid_bars}

        eq[i] = equity

    res = BacktestResult(trades=trades, equity_curve=pd.Series(eq, index=df.index).ffill(),
                         start_equity=start, end_equity=equity, cost=cost_name)
    return res


if __name__ == "__main__":
    print("FVG sniper entry — entry TF x bias TF x RR (realistic costs, full history)\n")
    months_cache = {}
    for entry_tf, bias_tf in [("15m", "4h"), ("5m", "1h"), ("5m", "4h"), ("15m", "1d")]:
        for rr in [2.0, 3.0, 5.0]:
            res = run_fvg(entry_tf=entry_tf, bias_tf=bias_tf, rr=rr)
            m = M.compute(res, entry_tf)
            mo = res.equity_curve.resample("ME").last().pct_change().dropna() * 100
            posmo = 100 * (mo > 0).mean() if len(mo) else 0
            yrs = (res.equity_curve.index[-1] - res.equity_curve.index[0]).days / 365.25
            print(f"{entry_tf}/{bias_tf} RR{rr} | trades {m['trades']:>4} ({m['trades']/yrs:>4.0f}/yr) | "
                  f"win% {m['win_rate']:>4} | expR {m['expectancy_R']:>6} | ret% {m['total_return_pct']:>7} | "
                  f"DD% {m['max_dd_pct']:>6} | +mo {posmo:>3.0f}%")

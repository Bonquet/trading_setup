"""
PART 3 — Order Blocks (mitigation entry).

On a structure break, find the order block (last opposite-color candle before the
impulse), then place a LIMIT at the OB and enter when price retraces to mitigate it.
Stop beyond the OB. Compares OB mitigation entry vs entering at the break.
Killzone filter included (built on Part 2).
"""
from __future__ import annotations
import numpy as np, pandas as pd
import data_loader, indicators as ind
from engine import Trade, BacktestResult, COST_SCENARIOS, USD_PER_LOT_PER_DOLLAR
import metrics as M


def run_ob(tf="1h", rr=3.0, ob_lookback=8, valid_bars=12, atr_buf=0.2,
           risk=0.01, start=10_000.0, cost_name="realistic", max_bars=80,
           use_kz=True, entry="ob"):
    df = data_loader.load(tf)
    ms = ind.market_structure(df, 3, 3)
    trend, last_sh, last_sl = ms["trend"], ms["last_sh"], ms["last_sl"]
    bos, choch = ms["bos"], ms["choch"]
    atr = ind.atr(df, 14).values
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    hour = df.index.hour.values
    n = len(df)
    cost = COST_SCENARIOS[cost_name]

    def in_kz(i):
        if not use_kz:
            return True
        return (7 <= hour[i] <= 10) or (12 <= hour[i] <= 15)

    equity = start
    eq = np.full(n, np.nan)
    trades = []
    pos = None
    pend = None

    for i in range(4, n):
        # manage open position
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
                pos.r_multiple = pnl / risk_d if risk_d > 0 else 0; pos.reason = reason
                equity += pnl; trades.append(pos); pos = None
            else:
                pos.bars_held += 1

        # check pending limit fill (mitigation)
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
                        lots = max(0.01, np.floor((equity * risk / (sd * USD_PER_LOT_PER_DOLLAR)) / 0.01) * 0.01)
                        tgt = fill + pend["dir"] * rr * sd
                        pos = Trade(direction=pend["dir"], entry_time=df.index[i], entry=fill,
                                    stop=pend["stop"], target=tgt, lots=lots, conf=1)
                    pend = None

        # detect structure break -> arm OB limit (or market entry)
        if pos is None and pend is None and (bos[i] or choch[i]) and in_kz(i):
            if trend[i] == 1:
                # bullish OB = last bearish candle in the lookback before the break
                ob_idx = None
                for j in range(i, max(2, i - ob_lookback), -1):
                    if c[j] < o[j]:
                        ob_idx = j; break
                if ob_idx is not None:
                    ob_top, ob_bot = h[ob_idx], l[ob_idx]
                    if entry == "ob":
                        limit = ob_top
                        stop = ob_bot - atr_buf * atr[i]
                        if limit - stop > 0:
                            pend = {"dir": 1, "limit": limit, "stop": stop, "expiry": i + valid_bars}
                    else:  # market entry at break (baseline)
                        entryp = c[i]; stop = ob_bot - atr_buf * atr[i]
                        sd = abs(entryp - stop)
                        if sd > 0:
                            lots = max(0.01, np.floor((equity * risk / (sd * USD_PER_LOT_PER_DOLLAR)) / 0.01) * 0.01)
                            pos = Trade(1, df.index[i], entryp, stop, entryp + rr * sd, lots, conf=1)
            elif trend[i] == -1:
                ob_idx = None
                for j in range(i, max(2, i - ob_lookback), -1):
                    if c[j] > o[j]:
                        ob_idx = j; break
                if ob_idx is not None:
                    ob_top, ob_bot = h[ob_idx], l[ob_idx]
                    if entry == "ob":
                        limit = ob_bot
                        stop = ob_top + atr_buf * atr[i]
                        if stop - limit > 0:
                            pend = {"dir": -1, "limit": limit, "stop": stop, "expiry": i + valid_bars}
                    else:
                        entryp = c[i]; stop = ob_top + atr_buf * atr[i]
                        sd = abs(entryp - stop)
                        if sd > 0:
                            lots = max(0.01, np.floor((equity * risk / (sd * USD_PER_LOT_PER_DOLLAR)) / 0.01) * 0.01)
                            pos = Trade(-1, df.index[i], entryp, stop, entryp - rr * sd, lots, conf=1)

        eq[i] = equity

    res = BacktestResult(trades=trades, equity_curve=pd.Series(eq, index=df.index).ffill(),
                         start_equity=start, end_equity=equity, cost=cost_name)
    return res


if __name__ == "__main__":
    print("PART 3 — Order Blocks: mitigation (OB limit) vs market-at-break, with killzones\n")
    for tf in ["15m", "1h"]:
        for rr in [2.0, 3.0]:
            base = run_ob(tf, rr=rr, entry="break")
            ob = run_ob(tf, rr=rr, entry="ob")
            mb, mo = M.compute(base, tf), M.compute(ob, tf)
            yrs = (base.equity_curve.index[-1] - base.equity_curve.index[0]).days / 365.25
            print(f"{tf} RR{rr}")
            print(f"   break entry (KZ) | trades {mb['trades']:>4} ({mb['trades']/yrs:>3.0f}/yr) | win% {mb['win_rate']:>4} | PF {mb['profit_factor']:>4} | expR {mb['expectancy_R']:>6} | ret% {mb['total_return_pct']:>7} | DD% {mb['max_dd_pct']:>6}")
            print(f"   OB mitigation    | trades {mo['trades']:>4} ({mo['trades']/yrs:>3.0f}/yr) | win% {mo['win_rate']:>4} | PF {mo['profit_factor']:>4} | expR {mo['expectancy_R']:>6} | ret% {mo['total_return_pct']:>7} | DD% {mo['max_dd_pct']:>6}")
            print()

"""
Slow trend timing model (the 'longer timeframe' candidate).

Classic moving-average timing (Faber-style) on weekly/monthly bars:
go long when close is above the trend SMA, flip short when below, exit/flip on the
opposite cross. Very few trades, captures gold's multi-month/year trends.
SMA length: 10 on Monthly, 40 on Weekly (~ same ~10-month horizon).
Initial stop 3*ATR (disaster stop / sizing). No fixed target.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

ATR_STOP = 3.0
ATR_TRAIL = 4.0
SMA_BY_TF = {"1M": 10, "1w": 40}


def generate(df, tf: str) -> dict:
    length = SMA_BY_TF.get(tf, 10)
    sma = ind.sma(df["Close"], length)
    atr = ind.atr(df, 14)
    c = df["Close"]

    cross_up = (c > sma) & (c.shift(1) <= sma.shift(1))
    cross_dn = (c < sma) & (c.shift(1) >= sma.shift(1))

    stop_long = c - ATR_STOP * atr
    stop_short = c + ATR_STOP * atr

    sig = empty_signals(df.index)
    sig.loc[cross_up, "dir"] = 1
    sig.loc[cross_dn, "dir"] = -1
    sig.loc[cross_up, "stop"] = stop_long[cross_up]
    sig.loc[cross_dn, "stop"] = stop_short[cross_dn]
    sig["target"] = np.nan
    sig["exit"] = cross_up | cross_dn

    return {"signals": sig, "atr_series": atr, "atr_trail_mult": ATR_TRAIL}

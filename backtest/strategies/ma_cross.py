"""
Moving-average crossover trend follower (always-in-market, stop-and-reverse).

Fast EMA vs slow EMA. Long on fast-above-slow cross, short on fast-below-slow cross.
Exit/flip on the opposite cross. Initial stop = 2.5*ATR (sizing + disaster stop).
3*ATR chandelier trailing. No fixed target.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

FAST = 50
SLOW = 200
ATR_STOP = 2.5
ATR_TRAIL = 3.0


def generate(df, tf: str) -> dict:
    fast = ind.ema(df["Close"], FAST)
    slow = ind.ema(df["Close"], SLOW)
    atr = ind.atr(df, 20)
    c = df["Close"]

    cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
    cross_dn = (fast < slow) & (fast.shift(1) >= slow.shift(1))

    stop_long = c - ATR_STOP * atr
    stop_short = c + ATR_STOP * atr

    sig = empty_signals(df.index)
    sig.loc[cross_up, "dir"] = 1
    sig.loc[cross_dn, "dir"] = -1
    sig.loc[cross_up, "stop"] = stop_long[cross_up]
    sig.loc[cross_dn, "stop"] = stop_short[cross_dn]
    sig["target"] = np.nan
    sig["exit"] = cross_up | cross_dn  # any cross closes the prior position

    return {"signals": sig, "atr_series": atr, "atr_trail_mult": ATR_TRAIL}

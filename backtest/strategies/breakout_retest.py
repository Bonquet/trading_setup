"""
Breakout + retest.

Price breaks above the prior 20-bar high (breakout), then within RETEST_WINDOW bars
pulls back to the broken level and closes back above it = long entry on the retest.
Mirror for downside. Stop below/above the retest extreme. Fixed 2R target.
This enters on the confirmation of a hold, not on the initial breakout spike.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import indicators as ind
from ._base import empty_signals

ENTRY_N = 20
RETEST_WINDOW = 6
RR = 2.0
ATR_BUF = 0.5
TREND_EMA = 200
MAX_BARS = 60


def generate(df, tf: str) -> dict:
    upper = df["High"].rolling(ENTRY_N).max().shift(1)
    lower = df["Low"].rolling(ENTRY_N).min().shift(1)
    atr = ind.atr(df, 14)
    trend = ind.ema(df["Close"], TREND_EMA)
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    up = upper.values
    lo = lower.values
    tr = trend.values
    av = atr.values
    n = len(df)

    dirs = np.zeros(n, int)
    stops = np.full(n, np.nan)
    targets = np.full(n, np.nan)

    # state machine: track a recent breakout level awaiting retest
    pend_up_level = np.nan
    pend_up_age = 0
    pend_dn_level = np.nan
    pend_dn_age = 0

    for i in range(1, n):
        # register fresh breakouts (with trend alignment)
        if not np.isnan(up[i]) and c[i] > up[i] and c[i] > tr[i]:
            pend_up_level = up[i]
            pend_up_age = 0
        if not np.isnan(lo[i]) and c[i] < lo[i] and c[i] < tr[i]:
            pend_dn_level = lo[i]
            pend_dn_age = 0

        # look for a retest of a pending up-breakout
        if not np.isnan(pend_up_level):
            pend_up_age += 1
            if l[i] <= pend_up_level and c[i] > pend_up_level and c[i] > o[i]:
                stop = l[i] - ATR_BUF * av[i]
                if c[i] - stop > 0:
                    dirs[i] = 1
                    stops[i] = stop
                    targets[i] = c[i] + RR * (c[i] - stop)
                pend_up_level = np.nan
            elif pend_up_age > RETEST_WINDOW:
                pend_up_level = np.nan

        if not np.isnan(pend_dn_level):
            pend_dn_age += 1
            if h[i] >= pend_dn_level and c[i] < pend_dn_level and c[i] < o[i]:
                stop = h[i] + ATR_BUF * av[i]
                if stop - c[i] > 0:
                    dirs[i] = -1
                    stops[i] = stop
                    targets[i] = c[i] - RR * (stop - c[i])
                pend_dn_level = np.nan
            elif pend_dn_age > RETEST_WINDOW:
                pend_dn_level = np.nan

    sig = empty_signals(df.index)
    sig["dir"] = dirs
    sig["stop"] = stops
    sig["target"] = targets
    return {"signals": sig, "max_bars": MAX_BARS}

"""
Donchian channel breakout (turtle-style trend follow).

Enter long when close breaks above the prior 20-bar high; short below the prior
20-bar low. Initial stop = 2*ATR (for sizing). Exit on opposite 10-bar channel
break (signal exit) plus a 3*ATR chandelier trailing stop. No fixed target.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

ENTRY_N = 20
EXIT_N = 10
ATR_STOP = 2.0
ATR_TRAIL = 3.0


def generate(df, tf: str) -> dict:
    upper, lower, _ = ind.donchian(df, ENTRY_N)
    exit_up, exit_low, _ = ind.donchian(df, EXIT_N)
    atr = ind.atr(df, 20)
    c = df["Close"]

    long_sig = c > upper
    short_sig = c < lower

    # signal exit: close crosses the opposite short-channel against the position.
    # We can't know direction here per-bar, so flag both; engine only acts when in a position.
    exit_long = c < exit_low
    exit_short = c > exit_up
    exit_flag = exit_long | exit_short

    stop_long = c - ATR_STOP * atr
    stop_short = c + ATR_STOP * atr

    sig = empty_signals(df.index)
    sig.loc[long_sig, "dir"] = 1
    sig.loc[short_sig, "dir"] = -1
    sig.loc[long_sig, "stop"] = stop_long[long_sig]
    sig.loc[short_sig, "stop"] = stop_short[short_sig]
    sig["target"] = np.nan
    sig["exit"] = exit_flag

    return {"signals": sig, "atr_series": atr, "atr_trail_mult": ATR_TRAIL}

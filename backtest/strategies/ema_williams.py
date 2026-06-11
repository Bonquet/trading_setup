"""
Playbook System 2 — 50 EMA Williams (mechanical).

LONG (all): close above 50 EMA-High channel, Williams %R crosses up through -20,
            Stochastic %K above %D and above 60, with HTF-trend bias (close > EMA200).
SHORT: mirror (below 50 EMA-Low, %R crosses down through -80, %K < %D and < 40, close < EMA200).
Stop: recent swing extreme +/- 0.5*ATR. Target: fixed 2R. Time stop: 50 bars.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

LOOKBACK = 10
RR = 2.0
ATR_BUF = 0.5
TREND_EMA = 200
MAX_BARS = 50


def generate(df, tf: str) -> dict:
    ch = ind.ema_channel(df, 50)
    wr = ind.williams_r(df, 14)
    k, d = ind.stochastic(df, 14, 3, 3)
    atr = ind.atr(df, 14)
    trend = ind.ema(df["Close"], TREND_EMA)
    roll_low = df["Low"].rolling(LOOKBACK).min()
    roll_high = df["High"].rolling(LOOKBACK).max()
    close = df["Close"]

    wr_cross_up = (wr > -20) & (wr.shift(1) <= -20)
    wr_cross_dn = (wr < -80) & (wr.shift(1) >= -80)

    long_sig = (
        (close > ch["ema_high"]) & wr_cross_up &
        (k > d) & (k > 60) & (close > trend)
    )
    short_sig = (
        (close < ch["ema_low"]) & wr_cross_dn &
        (k < d) & (k < 40) & (close < trend)
    )

    stop_long = roll_low - ATR_BUF * atr
    stop_short = roll_high + ATR_BUF * atr
    tgt_long = close + RR * (close - stop_long)
    tgt_short = close - RR * (stop_short - close)

    sig = empty_signals(df.index)
    sig.loc[long_sig, "dir"] = 1
    sig.loc[short_sig, "dir"] = -1
    sig.loc[long_sig, "stop"] = stop_long[long_sig]
    sig.loc[short_sig, "stop"] = stop_short[short_sig]
    sig.loc[long_sig, "target"] = tgt_long[long_sig]
    sig.loc[short_sig, "target"] = tgt_short[short_sig]

    return {"signals": sig, "max_bars": MAX_BARS}

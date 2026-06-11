"""
Playbook System 1 — Pullback (trend + retracement to dynamic support/resistance).

Trend via EMA stack (EMA50 vs EMA200). In an uptrend, wait for price to pull back
to the 50 EMA, then a bullish reversal candle that closes back above the 50 EMA and
above the prior bar's high = entry. Mirror for downtrend.
Stop: below/above the pullback swing +/- 0.5*ATR. Target: fixed 2R. Time stop: 60 bars.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

EMA_FAST = 50
EMA_SLOW = 200
LOOKBACK = 8
RR = 2.0
ATR_BUF = 0.5
TOL = 0.5      # ATR multiples: how close the pullback must get to the EMA
MAX_BARS = 60


def generate(df, tf: str) -> dict:
    ema_f = ind.ema(df["Close"], EMA_FAST)
    ema_s = ind.ema(df["Close"], EMA_SLOW)
    atr = ind.atr(df, 14)
    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    roll_low = df["Low"].rolling(LOOKBACK).min()
    roll_high = df["High"].rolling(LOOKBACK).max()

    uptrend = (ema_f > ema_s) & (c.shift(1) > ema_s)
    downtrend = (ema_f < ema_s) & (c.shift(1) < ema_s)

    # pullback touched the EMA this bar (low dipped to within TOL*ATR of EMA_fast)
    touched_up = (l <= ema_f + TOL * atr)
    touched_dn = (h >= ema_f - TOL * atr)

    # bullish reversal close back above EMA and above prior high
    bull_confirm = (c > o) & (c > ema_f) & (c > h.shift(1))
    bear_confirm = (c < o) & (c < ema_f) & (c < l.shift(1))

    long_sig = uptrend & touched_up & bull_confirm
    short_sig = downtrend & touched_dn & bear_confirm

    stop_long = roll_low - ATR_BUF * atr
    stop_short = roll_high + ATR_BUF * atr
    tgt_long = c + RR * (c - stop_long)
    tgt_short = c - RR * (stop_short - c)

    sig = empty_signals(df.index)
    sig.loc[long_sig, "dir"] = 1
    sig.loc[short_sig, "dir"] = -1
    sig.loc[long_sig, "stop"] = stop_long[long_sig]
    sig.loc[short_sig, "stop"] = stop_short[short_sig]
    sig.loc[long_sig, "target"] = tgt_long[long_sig]
    sig.loc[short_sig, "target"] = tgt_short[short_sig]

    return {"signals": sig, "max_bars": MAX_BARS}

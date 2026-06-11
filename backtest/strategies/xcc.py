"""
XCC — XAUUSD Compression Continuation.

Designed from scratch by studying 22 years of gold data (2004-2026):
  * Gold has structural positive drift (+0.05%/day baseline)
  * Daily mean reversion: 3-down days bounce, 3-up days fade
  * Range compression precedes the biggest expansions
  * Inside days lean modestly long
  * Trend filter (Close > EMA200 + EMA50 rising) DOUBLES the edge

Rules:
  - Timeframe: D1 only (edge dies on H4/H1)
  - Trend filter (must be true on signal bar):
      Close > EMA200  AND  EMA50 > EMA50.shift(10)  (uptrend confirmed)
  - Entry triggers (any one of):
      A. RANGE_COMPRESS: range < 0.5 * ATR(20)         — quiet day before expansion
      B. THREE_DOWN:     3 consecutive down closes      — oversold bounce
      C. INSIDE_DAY:     high < prior high AND low > prior low
  - Stop:    swing low (10 bars) - 0.5 * ATR(14)
  - Target:  2R fixed (matches the +0.95% / 5-day expected move)
  - Time exit: 50 bars (safety net)

Backtest performance (target — to be confirmed by engine):
  ~140-200 trades over 22 years (selective)
  Expected: 60%+ win rate, 1.7-2.0 PF, low drawdown
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import indicators as ind
from ._base import empty_signals

# Indicator parameters
EMA_TREND       = 200
EMA_SLOPE_LOOK  = 10
EMA_RISING      = 50
ATR_PERIOD      = 14
RANGE_LOOK      = 20
SWING_LOOK      = 10
ATR_STOP_BUF    = 0.5
RR              = 2.0
MAX_BARS        = 50


def generate(df: pd.DataFrame, tf: str) -> dict:
    """Generate XCC signals for a given OHLC DataFrame."""
    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]
    op    = df["Open"]

    ema200 = ind.ema(close, EMA_TREND)
    ema50  = ind.ema(close, EMA_RISING)
    atr14  = ind.atr(df, ATR_PERIOD)
    atr20  = (high - low).rolling(RANGE_LOOK).mean()

    # === Trend filter ===
    in_uptrend = (close > ema200) & (ema50 > ema50.shift(EMA_SLOPE_LOOK))

    # === Three entry triggers ===
    range_today = high - low
    trigger_A_compress  = range_today < 0.5 * atr20
    ret = close.pct_change()
    trigger_B_three_dn  = (ret < 0) & (ret.shift(1) < 0) & (ret.shift(2) < 0)
    trigger_C_inside    = (high < high.shift(1)) & (low > low.shift(1))

    any_trigger = trigger_A_compress | trigger_B_three_dn | trigger_C_inside

    # === Long signal: any trigger AND uptrend ===
    long_sig = any_trigger & in_uptrend

    # === Stop & target ===
    swing_low = low.rolling(SWING_LOOK).min()
    stop_long = swing_low - ATR_STOP_BUF * atr14
    risk = close - stop_long
    tgt_long = close + RR * risk

    sig = empty_signals(df.index)
    sig.loc[long_sig, "dir"] = 1
    sig.loc[long_sig, "stop"]   = stop_long[long_sig]
    sig.loc[long_sig, "target"] = tgt_long[long_sig]

    return {"signals": sig, "max_bars": MAX_BARS}

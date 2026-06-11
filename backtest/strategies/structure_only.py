"""
PART 1 — Market Structure ONLY (BOS / CHoCH).

No EMA, no momentum, no FVG, no liquidity. Pure structure:
  * Detect swings (fractals, left/right configurable = how "big" a swing must be).
  * A bullish break of structure (close breaks last swing high) -> go LONG.
  * A bearish break (close breaks last swing low) -> go SHORT.
  * Stop = the protected swing on the other side. Target = fixed RR.
  * mode: 'all' = trade BOS + CHoCH, 'bos' = continuation only, 'choch' = reversal only.

This isolates the structure component so we can see its standalone edge per TF.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals


def generate(df, tf: str, left: int = 2, right: int = 2, rr: float = 2.0,
             atr_buf: float = 0.5, mode: str = "all", max_bars: int = 80,
             fixed_stop: float = 0.0, body_atr_min: float = 0.0,
             vol_mult: float = 0.0) -> dict:
    """fixed_stop > 0 uses a fixed $ stop distance instead of swing stop.
    body_atr_min > 0  : require break-candle body >= body_atr_min * ATR (displacement filter).
    vol_mult     > 0  : require break-candle volume >= vol_mult * SMA(volume,20)."""
    ms = ind.market_structure(df, left, right)
    trend, last_sh, last_sl = ms["trend"], ms["last_sh"], ms["last_sl"]
    bos, choch = ms["bos"], ms["choch"]
    atr = ind.atr(df, 14).values
    c = df["Close"].values
    o = df["Open"].values
    vol = df["Volume"].values
    vol_ma = df["Volume"].rolling(20).mean().values
    n = len(df)

    dirs = np.zeros(n, int)
    stops = np.full(n, np.nan)
    targets = np.full(n, np.nan)

    take_bos = mode in ("all", "bos")
    take_choch = mode in ("all", "choch")

    for i in range(n):
        event = (bos[i] and take_bos) or (choch[i] and take_choch)
        if not event:
            continue
        # displacement / body filter
        if body_atr_min > 0:
            if atr[i] <= 0 or abs(c[i] - o[i]) < body_atr_min * atr[i]:
                continue
        # volume confirmation filter
        if vol_mult > 0:
            if np.isnan(vol_ma[i]) or vol_ma[i] <= 0 or vol[i] < vol_mult * vol_ma[i]:
                continue
        if trend[i] == 1 and not np.isnan(last_sl[i]):
            stop = c[i] - fixed_stop if fixed_stop > 0 else last_sl[i] - atr_buf * atr[i]
            if c[i] - stop > 0:
                dirs[i] = 1; stops[i] = stop; targets[i] = c[i] + rr * (c[i] - stop)
        elif trend[i] == -1 and not np.isnan(last_sh[i]):
            stop = c[i] + fixed_stop if fixed_stop > 0 else last_sh[i] + atr_buf * atr[i]
            if stop - c[i] > 0:
                dirs[i] = -1; stops[i] = stop; targets[i] = c[i] - rr * (stop - c[i])

    sig = empty_signals(df.index)
    sig["dir"] = dirs
    sig["stop"] = stops
    sig["target"] = targets
    return {"signals": sig, "max_bars": max_bars}

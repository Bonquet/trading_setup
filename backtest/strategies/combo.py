"""
COMBO — Trend-Filtered SMC with Momentum Confirmation (the synthesis bot).

Combines the three things that survived testing, each covering the others' gaps:
  * TREND BACKBONE (most robust edge): 50 EMA > 200 EMA = bullish regime (mirror short).
    -> removes SMC's counter-trend losers and keeps us on the durable side.
  * SMC ENTRY TIMING: liquidity sweep of the latest swing + CHoCH/BOS back with trend.
    -> better entries than a raw MA cross (tighter stop, cleaner RR).
  * MOMENTUM CONFIRMATION (playbook 50 EMA Williams): Williams %R + Stochastic agree.
    -> filters weak/exhausted entries.
Stop beyond the liquidity sweep; target fixed 2R. 4H is the design timeframe.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import data_loader
import indicators as ind
from ._base import empty_signals

EMA_FAST = 50
EMA_SLOW = 200
RR = 2.0
SWEEP_WINDOW = 12
ATR_BUF = 0.3
WILLIAMS_LONG = -50.0   # %R above this = bullish momentum
WILLIAMS_SHORT = -50.0  # %R below this = bearish momentum
MAX_BARS = 80


def generate(df, tf: str) -> dict:
    ema_f = ind.ema(df["Close"], EMA_FAST).values
    ema_s = ind.ema(df["Close"], EMA_SLOW).values
    wr = ind.williams_r(df, 14).values
    k, d = ind.stochastic(df, 14, 3, 3)
    k = k.values; d = d.values
    atr = ind.atr(df, 14).values
    ms = ind.market_structure(df, left=2, right=2)
    last_sh, last_sl = ms["last_sh"], ms["last_sl"]
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    n = len(df)

    dirs = np.zeros(n, int)
    stops = np.full(n, np.nan)
    targets = np.full(n, np.nan)

    pend_long = False; pl_age = 0; sweep_low = np.nan; ref_sh = np.nan
    pend_short = False; ps_age = 0; sweep_high = np.nan; ref_sl = np.nan

    for i in range(2, n):
        bull_regime = ema_f[i] > ema_s[i]
        bear_regime = ema_f[i] < ema_s[i]
        sl_prev = last_sl[i - 1]
        sh_prev = last_sh[i - 1]

        # SMC liquidity sweep, only in-trend
        if bull_regime and not np.isnan(sl_prev) and l[i] < sl_prev and c[i] > sl_prev:
            pend_long = True; pl_age = 0; sweep_low = l[i]; ref_sh = sh_prev
        if bear_regime and not np.isnan(sh_prev) and h[i] > sh_prev and c[i] < sh_prev:
            pend_short = True; ps_age = 0; sweep_high = h[i]; ref_sl = sl_prev

        # confirm long: CHoCH/BOS up + momentum agreement
        if pend_long:
            pl_age += 1
            momentum_ok = (wr[i] > WILLIAMS_LONG) and (k[i] > d[i])
            if not np.isnan(ref_sh) and c[i] > ref_sh and momentum_ok and ema_f[i] > ema_s[i]:
                stop = sweep_low - ATR_BUF * atr[i]
                if c[i] - stop > 0:
                    dirs[i] = 1; stops[i] = stop; targets[i] = c[i] + RR * (c[i] - stop)
                pend_long = False
            elif pl_age > SWEEP_WINDOW:
                pend_long = False

        if pend_short:
            ps_age += 1
            momentum_ok = (wr[i] < WILLIAMS_SHORT) and (k[i] < d[i])
            if not np.isnan(ref_sl) and c[i] < ref_sl and momentum_ok and ema_f[i] < ema_s[i]:
                stop = sweep_high + ATR_BUF * atr[i]
                if stop - c[i] > 0:
                    dirs[i] = -1; stops[i] = stop; targets[i] = c[i] - RR * (stop - c[i])
                pend_short = False
            elif ps_age > SWEEP_WINDOW:
                pend_short = False

    sig = empty_signals(df.index)
    sig["dir"] = dirs
    sig["stop"] = stops
    sig["target"] = targets
    return {"signals": sig, "max_bars": MAX_BARS}

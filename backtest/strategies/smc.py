"""
Smart Money Concepts (SMC) — faithful mechanical implementation.

Methodology (from SMC/ICT literature, gold day-trading variant):
  1. HTF BIAS: higher-timeframe market structure (4H for 15m/30m/1h entries,
     Daily for 4H entries). Trade only in the HTF trend direction.
  2. LIQUIDITY SWEEP: on the entry TF, price grabs liquidity by wicking beyond the
     latest confirmed swing low (longs) / high (shorts), then closes back inside.
  3. CHoCH / BOS: structure shifts back with trend — close breaks the reference
     swing high (long) / low (short) created before the sweep.
  4. ENTRY: on that confirmation close (confirmation-entry variant).
  5. STOP: just beyond the sweep extreme (the liquidity grab low/high).
  6. TARGET: 1:2 RR (SMC minimum), i.e. opposing-liquidity-style target.

Entry timeframes tested: 15m, 30m, 1h (HTF bias 4H); 4h (HTF bias Daily).
Note: this is the *confirmation-entry* variant. A stricter FVG/order-block limit
entry in the discount/premium zone would change fill rate and RR (future variant).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import data_loader
import indicators as ind
from ._base import empty_signals

BIAS_TF = {"15m": "4h", "30m": "4h", "1h": "4h", "4h": "1d"}
TF_HOURS = {"4h": 4, "1d": 24}
RR = 2.0
SWEEP_WINDOW = 12     # bars allowed between sweep and CHoCH confirmation
ATR_BUF = 0.3
MAX_BARS = 80


def generate(df, tf: str) -> dict:
    bias_tf = BIAS_TF.get(tf, "4h")
    htf = data_loader.load(bias_tf)
    htf = htf[(htf.index >= df.index[0] - pd.Timedelta(days=15)) & (htf.index <= df.index[-1])]
    bias = ind.htf_bias_aligned(df.index, htf, TF_HOURS[bias_tf])

    ms = ind.market_structure(df, left=2, right=2)
    last_sh, last_sl = ms["last_sh"], ms["last_sl"]
    atr = ind.atr(df, 14).values
    o, h, l, c = df["Open"].values, df["High"].values, df["Low"].values, df["Close"].values
    n = len(df)

    dirs = np.zeros(n, int)
    stops = np.full(n, np.nan)
    targets = np.full(n, np.nan)

    pend_long = False; pl_age = 0; sweep_low = np.nan; ref_sh = np.nan
    pend_short = False; ps_age = 0; sweep_high = np.nan; ref_sl = np.nan

    for i in range(2, n):
        sl_prev = last_sl[i - 1]
        sh_prev = last_sh[i - 1]

        # liquidity sweep (arm a pending setup)
        if bias[i] == 1 and not np.isnan(sl_prev) and l[i] < sl_prev and c[i] > sl_prev:
            pend_long = True; pl_age = 0; sweep_low = l[i]; ref_sh = sh_prev
        if bias[i] == -1 and not np.isnan(sh_prev) and h[i] > sh_prev and c[i] < sh_prev:
            pend_short = True; ps_age = 0; sweep_high = h[i]; ref_sl = sl_prev

        # confirm long on CHoCH/BOS up
        if pend_long:
            pl_age += 1
            if not np.isnan(ref_sh) and c[i] > ref_sh:
                stop = sweep_low - ATR_BUF * atr[i]
                if c[i] - stop > 0:
                    dirs[i] = 1; stops[i] = stop; targets[i] = c[i] + RR * (c[i] - stop)
                pend_long = False
            elif pl_age > SWEEP_WINDOW:
                pend_long = False

        if pend_short:
            ps_age += 1
            if not np.isnan(ref_sl) and c[i] < ref_sl:
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

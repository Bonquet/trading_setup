"""
COMBO-SMALL — H1 small-account version.

Fixes the H4 bot's "sat out the rally" bug by adding a TREND-CONTINUATION PULLBACK
entry (doesn't need a liquidity sweep), alongside the SMC sweep entry. Both are
trend-filtered + momentum-confirmed. Supports compressed (tighter) stops for
shorter trades and small-account dollar risk.

generate(df, tf, ...) params let us sweep stop sizes in the backtest.
"""
from __future__ import annotations

import numpy as np

import indicators as ind
from ._base import empty_signals

EMA_FAST = 50
EMA_SLOW = 200
SWEEP_WINDOW = 12
WILLIAMS = -50.0
MAX_BARS = 60


def generate(df, tf: str,
             stop_mode: str = "atr",     # 'atr' or 'fixed'
             stop_atr: float = 1.2,       # ATR multiple (compressed)
             stop_fixed: float = 5.0,     # fixed $ stop distance
             stop_max: float = 0.0,       # cap stop distance in $ (0 = off)
             rr: float = 2.0,
             use_sweep: bool = True,
             use_pullback: bool = True,
             use_williams: bool = True,
             use_stoch: bool = True) -> dict:
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
    conf = np.zeros(n, int)   # 1 = sure (high confluence), 0 = unsure

    pend_long = False; pl_age = 0; sweep_low = np.nan; ref_sh = np.nan
    pend_short = False; ps_age = 0; sweep_high = np.nan; ref_sl = np.nan

    def mk_stop_long(i, struct_low):
        s = c[i] - stop_fixed if stop_mode == "fixed" else struct_low - stop_atr * atr[i]
        if stop_max > 0 and (c[i] - s) > stop_max:   # clip wide outliers
            s = c[i] - stop_max
        return s

    def mk_stop_short(i, struct_high):
        s = c[i] + stop_fixed if stop_mode == "fixed" else struct_high + stop_atr * atr[i]
        if stop_max > 0 and (s - c[i]) > stop_max:
            s = c[i] + stop_max
        return s

    def emit_long(i, struct_low, sure):
        stop = mk_stop_long(i, struct_low)
        if c[i] - stop > 0:
            dirs[i] = 1; stops[i] = stop; targets[i] = c[i] + rr * (c[i] - stop)
            conf[i] = 1 if sure else 0

    def emit_short(i, struct_high, sure):
        stop = mk_stop_short(i, struct_high)
        if stop - c[i] > 0:
            dirs[i] = -1; stops[i] = stop; targets[i] = c[i] - rr * (stop - c[i])
            conf[i] = 1 if sure else 0

    for i in range(2, n):
        bull = ema_f[i] > ema_s[i]
        bear = ema_f[i] < ema_s[i]
        mom_long = mom_short = True
        if use_williams:
            mom_long = mom_long and (wr[i] > WILLIAMS)
            mom_short = mom_short and (wr[i] < WILLIAMS)
        if use_stoch:
            mom_long = mom_long and (k[i] > d[i])
            mom_short = mom_short and (k[i] < d[i])

        # ---- SMC sweep arming ----
        if use_sweep:
            sl_prev = last_sl[i - 1]; sh_prev = last_sh[i - 1]
            if bull and not np.isnan(sl_prev) and l[i] < sl_prev and c[i] > sl_prev:
                pend_long = True; pl_age = 0; sweep_low = l[i]; ref_sh = sh_prev
            if bear and not np.isnan(sh_prev) and h[i] > sh_prev and c[i] < sh_prev:
                pend_short = True; ps_age = 0; sweep_high = h[i]; ref_sl = sl_prev

        if dirs[i] == 0 and use_sweep and pend_long:
            pl_age += 1
            if not np.isnan(ref_sh) and c[i] > ref_sh and mom_long and bull:
                emit_long(i, sweep_low, sure=True)   # full confluence = sure
                pend_long = False
            elif pl_age > SWEEP_WINDOW:
                pend_long = False
        if dirs[i] == 0 and use_sweep and pend_short:
            ps_age += 1
            if not np.isnan(ref_sl) and c[i] < ref_sl and mom_short and bear:
                emit_short(i, sweep_high, sure=True)
                pend_short = False
            elif ps_age > SWEEP_WINDOW:
                pend_short = False

        # ---- trend-continuation pullback entry (anti-drought) ----
        if dirs[i] == 0 and use_pullback:
            if (bull and l[i] <= ema_f[i] and c[i] > ema_f[i] and c[i] > o[i] and mom_long):
                emit_long(i, min(l[i], l[i - 1]), sure=False)   # continuation = unsure
            elif (bear and h[i] >= ema_f[i] and c[i] < ema_f[i] and c[i] < o[i] and mom_short):
                emit_short(i, max(h[i], h[i - 1]), sure=False)

    sig = empty_signals(df.index)
    sig["dir"] = dirs
    sig["stop"] = stops
    sig["target"] = targets
    sig["conf"] = conf
    return {"signals": sig, "max_bars": MAX_BARS}

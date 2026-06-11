"""
indicators.py — vectorized technical indicators for the backtest lab.

All functions take/return pandas Series/DataFrame aligned to the input index.
Designed for trend-following + the playbook's 50 EMA Williams / Pullback systems.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def ema_channel(df: pd.DataFrame, period: int = 50) -> pd.DataFrame:
    """Playbook's '50 EMA High' / '50 EMA Low' channel."""
    return pd.DataFrame({
        "ema_high": ema(df["High"], period),
        "ema_low": ema(df["Low"], period),
    }, index=df.index)


def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hh = df["High"].rolling(period).max()
    ll = df["Low"].rolling(period).min()
    wr = -100 * (hh - df["Close"]) / (hh - ll).replace(0, np.nan)
    return wr


def stochastic(df: pd.DataFrame, k: int = 14, d: int = 3, smooth_k: int = 3):
    ll = df["Low"].rolling(k).min()
    hh = df["High"].rolling(k).max()
    raw_k = 100 * (df["Close"] - ll) / (hh - ll).replace(0, np.nan)
    k_line = raw_k.rolling(smooth_k).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / period, adjust=False).mean()


def donchian(df: pd.DataFrame, period: int = 20):
    """Upper/lower Donchian channels using PRIOR bars (shifted to avoid look-ahead)."""
    upper = df["High"].rolling(period).max().shift(1)
    lower = df["Low"].rolling(period).min().shift(1)
    mid = (upper + lower) / 2
    return upper, lower, mid


def parabolic_sar(df: pd.DataFrame, af_step: float = 0.02, af_max: float = 0.2) -> pd.Series:
    """Wilder's Parabolic SAR (iterative)."""
    high = df["High"].values
    low = df["Low"].values
    n = len(df)
    sar = np.full(n, np.nan)
    if n < 2:
        return pd.Series(sar, index=df.index)

    # init: assume initial uptrend
    bull = True
    af = af_step
    ep = high[0]
    sar[0] = low[0]

    for i in range(1, n):
        prev_sar = sar[i - 1]
        if bull:
            cur = prev_sar + af * (ep - prev_sar)
            cur = min(cur, low[i - 1], low[i - 2] if i >= 2 else low[i - 1])
            if low[i] < cur:  # flip to bear
                bull = False
                cur = ep
                ep = low[i]
                af = af_step
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + af_step, af_max)
        else:
            cur = prev_sar + af * (ep - prev_sar)
            cur = max(cur, high[i - 1], high[i - 2] if i >= 2 else high[i - 1])
            if high[i] > cur:  # flip to bull
                bull = True
                cur = ep
                ep = high[i]
                af = af_step
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + af_step, af_max)
        sar[i] = cur

    return pd.Series(sar, index=df.index)


def swing_points(df: pd.DataFrame, left: int = 2, right: int = 2):
    """
    Fractal swing highs/lows confirmed with `right` bars to the right.
    Returns two Series of price levels (NaN where no swing), shifted so the
    value is only known AFTER confirmation (no look-ahead).
    """
    high = df["High"]
    low = df["Low"]
    n = len(df)
    sh = np.full(n, np.nan)
    sl = np.full(n, np.nan)
    h = high.values
    l = low.values
    for i in range(left, n - right):
        window_h = h[i - left:i + right + 1]
        window_l = l[i - left:i + right + 1]
        if h[i] == window_h.max() and (window_h == h[i]).sum() == 1:
            sh[i] = h[i]
        if l[i] == window_l.min() and (window_l == l[i]).sum() == 1:
            sl[i] = l[i]
    sh = pd.Series(sh, index=df.index)
    sl = pd.Series(sl, index=df.index)
    # Confirmation only available `right` bars later -> shift forward
    return sh.shift(right), sl.shift(right)


def adx(df: pd.DataFrame, period: int = 14):
    """Wilder ADX with +DI/-DI. Returns (adx, plus_di, minus_di)."""
    up = df["High"].diff()
    down = -df["Low"].diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = true_range(df)
    atr_ = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_ = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx_, plus_di, minus_di


def market_structure(df: pd.DataFrame, left: int = 2, right: int = 2):
    """
    SMC market-structure engine. Detects swing points (fractals, confirmed `right`
    bars later -> no look-ahead) and tracks trend via BOS / CHoCH on closes.

    Returns dict of numpy arrays (len == len(df)):
        trend   : running +1 (bullish) / -1 (bearish) / 0
        last_sh : most recent CONFIRMED swing-high price (running)
        last_sl : most recent CONFIRMED swing-low price (running)
        choch   : bool, a Change-of-Character happened on this bar
        bos     : bool, a Break-of-Structure (continuation) happened on this bar
    """
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values
    n = len(df)

    # confirmed swing values become known at index i+right
    sh_at = np.full(n, np.nan)
    sl_at = np.full(n, np.nan)
    for i in range(left, n - right):
        wh = h[i - left:i + right + 1]
        wl = l[i - left:i + right + 1]
        if h[i] == wh.max() and (wh == h[i]).sum() == 1:
            sh_at[i + right] = h[i]
        if l[i] == wl.min() and (wl == l[i]).sum() == 1:
            sl_at[i + right] = l[i]

    trend = np.zeros(n, int)
    last_sh = np.full(n, np.nan)
    last_sl = np.full(n, np.nan)
    choch = np.zeros(n, bool)
    bos = np.zeros(n, bool)

    cur = 0
    sh = np.nan
    sl = np.nan
    sh_broken = False
    sl_broken = False
    for i in range(n):
        if not np.isnan(sh_at[i]):
            sh = sh_at[i]
            sh_broken = False
        if not np.isnan(sl_at[i]):
            sl = sl_at[i]
            sl_broken = False

        if not np.isnan(sh) and not sh_broken and c[i] > sh:
            if cur == 1:
                bos[i] = True
            else:
                choch[i] = True
            cur = 1
            sh_broken = True
        elif not np.isnan(sl) and not sl_broken and c[i] < sl:
            if cur == -1:
                bos[i] = True
            else:
                choch[i] = True
            cur = -1
            sl_broken = True

        trend[i] = cur
        last_sh[i] = sh
        last_sl[i] = sl

    return {"trend": trend, "last_sh": last_sh, "last_sl": last_sl,
            "choch": choch, "bos": bos}


def htf_bias_aligned(entry_index, htf_df: pd.DataFrame, tf_hours: float,
                     left: int = 2, right: int = 2) -> np.ndarray:
    """
    Compute HTF trend on htf_df and align it to entry_index WITHOUT look-ahead:
    each HTF bar's structure is only usable after the bar has closed
    (timestamp + tf_hours). Returns +1/-1/0 array aligned to entry_index.
    """
    ms = market_structure(htf_df, left, right)
    htf_trend = pd.Series(ms["trend"], index=htf_df.index)
    # shift timestamps to bar-close so info is only available after close
    htf_trend.index = htf_trend.index + pd.Timedelta(hours=tf_hours)
    aligned = htf_trend.reindex(
        htf_trend.index.union(entry_index)).sort_index().ffill().reindex(entry_index)
    return aligned.fillna(0).values.astype(int)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


if __name__ == "__main__":
    import data_loader
    df = data_loader.load("1d")
    ch = ema_channel(df, 50)
    wr = williams_r(df)
    k, d = stochastic(df)
    a = atr(df)
    print("Sample (last 3 daily bars):")
    out = pd.DataFrame({
        "Close": df["Close"], "ema_hi": ch["ema_high"], "ema_lo": ch["ema_low"],
        "willR": wr, "stochK": k, "stochD": d, "atr": a,
    }).tail(3)
    print(out.round(2).to_string())

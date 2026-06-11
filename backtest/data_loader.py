"""
data_loader.py — robust loader for the XAUUSD CSVs.

CSV format: Date;Open;High;Low;Close;Volume
Date format: YYYY.MM.DD HH:MM
Source dir : C:\\Users\\acebl\\Downloads\\XAU_<tf>_data.csv

Loads, validates, and caches to parquet for fast re-reads.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

DOWNLOADS = Path(r"C:\Users\acebl\Downloads")
CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Logical timeframe name -> CSV filename
TF_FILES = {
    "1m":   "XAU_1m_data.csv",
    "5m":   "XAU_5m_data.csv",
    "15m":  "XAU_15m_data.csv",
    "30m":  "XAU_30m_data.csv",
    "1h":   "XAU_1h_data.csv",
    "4h":   "XAU_4h_data.csv",
    "1d":   "XAU_1d_data.csv",
    "1w":   "XAU_1w_data.csv",
    "1M":   "XAU_1Month_data.csv",
}

# Rough bars-per-year, used only for CAGR / annualization helpers
BARS_PER_YEAR = {
    "1m": 525600, "5m": 105120, "15m": 35040, "30m": 17520,
    "1h": 8760, "4h": 2190, "1d": 365, "1w": 52, "1M": 12,
}


def _csv_path(tf: str) -> Path:
    if tf not in TF_FILES:
        raise ValueError(f"Unknown timeframe '{tf}'. Choices: {list(TF_FILES)}")
    return DOWNLOADS / TF_FILES[tf]


def load(tf: str, use_cache: bool = True) -> pd.DataFrame:
    """Return a clean OHLCV DataFrame indexed by datetime (ascending, deduped)."""
    cache = CACHE_DIR / f"{tf}.parquet"
    src = _csv_path(tf)

    if use_cache and cache.exists() and cache.stat().st_mtime >= src.stat().st_mtime:
        return pd.read_parquet(cache)

    df = pd.read_csv(
        src,
        sep=";",
        header=0,
        names=["Date", "Open", "High", "Low", "Close", "Volume"],
        dtype={"Open": "float64", "High": "float64", "Low": "float64",
               "Close": "float64", "Volume": "float64"},
    )
    df["Date"] = pd.to_datetime(df["Date"], format="%Y.%m.%d %H:%M")
    df = df.set_index("Date").sort_index()
    df = df[~df.index.duplicated(keep="first")]

    # Basic integrity: drop rows with non-positive prices or NaNs
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df = df[(df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
    # High/Low sanity
    df = df[(df["High"] >= df["Low"])]

    try:
        df.to_parquet(cache)
    except Exception as e:  # caching is best-effort
        print(f"[data_loader] cache write skipped for {tf}: {e}")

    return df


def summary(tf: str) -> dict:
    df = load(tf)
    return {
        "tf": tf,
        "rows": len(df),
        "start": df.index.min(),
        "end": df.index.max(),
        "first_close": float(df["Close"].iloc[0]),
        "last_close": float(df["Close"].iloc[-1]),
    }


if __name__ == "__main__":
    for tf in ["1M", "1w", "1d", "4h", "1h"]:
        s = summary(tf)
        print(f"{s['tf']:>3} | rows={s['rows']:>7} | {s['start']} -> {s['end']} | "
              f"close {s['first_close']:.1f} -> {s['last_close']:.1f}")

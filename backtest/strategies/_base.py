"""Shared helpers for strategies."""
from __future__ import annotations

import numpy as np
import pandas as pd


def empty_signals(index) -> pd.DataFrame:
    return pd.DataFrame({
        "dir": 0,
        "stop": np.nan,
        "target": np.nan,
        "exit": False,
    }, index=index)


def swing_stop_long(df: pd.DataFrame, i: int, lookback: int, buf: float) -> float:
    lo = df["Low"].iloc[max(0, i - lookback):i + 1].min()
    return lo - buf


def swing_stop_short(df: pd.DataFrame, i: int, lookback: int, buf: float) -> float:
    hi = df["High"].iloc[max(0, i - lookback):i + 1].max()
    return hi + buf


def target_from_rr(entry: float, stop: float, direction: int, rr: float) -> float:
    dist = abs(entry - stop)
    return entry + direction * rr * dist

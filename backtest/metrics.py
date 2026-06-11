"""
metrics.py — performance statistics from a BacktestResult.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from data_loader import BARS_PER_YEAR


def compute(res, tf: str) -> dict:
    trades = res.trades
    n = len(trades)
    eq = res.equity_curve

    if n == 0:
        return {
            "trades": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_R": 0.0,
            "total_return_pct": (res.end_equity / res.start_equity - 1) * 100,
            "cagr_pct": 0.0, "max_dd_pct": 0.0, "mar": 0.0, "sharpe": 0.0,
            "avg_R": 0.0, "best_R": 0.0, "worst_R": 0.0,
            "max_loss_streak": 0, "avg_bars": 0.0, "end_equity": res.end_equity,
        }

    pnls = np.array([t.pnl for t in trades])
    rs = np.array([t.r_multiple for t in trades])
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]

    win_rate = len(wins) / n * 100
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    profit_factor = gross_win / gross_loss if gross_loss > 0 else np.inf

    # drawdown on equity curve
    running_max = eq.cummax()
    dd = (eq - running_max) / running_max
    max_dd = dd.min() * 100

    # CAGR
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = ((res.end_equity / res.start_equity) ** (1 / years) - 1) * 100 if years > 0 and res.end_equity > 0 else 0.0

    # Sharpe from per-bar equity returns, annualized
    rets = eq.pct_change().dropna()
    bpy = BARS_PER_YEAR.get(tf, 252)
    if rets.std() > 0:
        sharpe = rets.mean() / rets.std() * np.sqrt(bpy)
    else:
        sharpe = 0.0

    # longest losing streak
    streak = max_streak = 0
    for p in pnls:
        if p < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    mar = cagr / abs(max_dd) if max_dd != 0 else 0.0

    return {
        "trades": n,
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if np.isfinite(profit_factor) else 999.0,
        "expectancy_R": round(rs.mean(), 3),
        "total_return_pct": round((res.end_equity / res.start_equity - 1) * 100, 1),
        "cagr_pct": round(cagr, 1),
        "max_dd_pct": round(max_dd, 1),
        "mar": round(mar, 2),
        "sharpe": round(sharpe, 2),
        "avg_R": round(rs.mean(), 2),
        "best_R": round(rs.max(), 2),
        "worst_R": round(rs.min(), 2),
        "max_loss_streak": int(max_streak),
        "avg_bars": round(np.mean([t.bars_held for t in trades]), 1),
        "end_equity": round(res.end_equity, 0),
    }


def trades_to_df(res) -> pd.DataFrame:
    rows = []
    for t in res.trades:
        rows.append({
            "dir": "LONG" if t.direction == 1 else "SHORT",
            "entry_time": t.entry_time, "entry": round(t.entry, 2),
            "stop": round(t.stop, 2),
            "target": round(t.target, 2) if not np.isnan(t.target) else None,
            "exit_time": t.exit_time, "exit": round(t.exit, 2) if t.exit else None,
            "lots": round(t.lots, 2), "pnl": round(t.pnl, 2),
            "R": round(t.r_multiple, 2), "reason": t.reason, "bars": t.bars_held,
        })
    return pd.DataFrame(rows)

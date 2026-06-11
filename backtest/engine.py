"""
engine.py — event-driven backtester for XAUUSD.

A strategy produces a signal DataFrame aligned to the price index with columns:
    dir    : desired entry direction decided at this bar's close (+1 long / -1 short / 0)
    stop   : absolute stop price for that entry
    target : absolute take-profit price, or NaN when using a signal-based exit
    exit   : bool, force-close an open position (signal-based exit)

Execution model (no look-ahead):
    * Signals are decided on a CLOSED bar i, acted on at bar i+1's OPEN.
    * Intrabar SL/TP are checked against bar high/low; if both are touched in the
      same bar, the STOP is assumed hit first (conservative).
    * Optional ATR chandelier trailing stop, managed by the engine.
    * Position sizing: risk `risk_pct` of current equity / stop distance.

XAUUSD contract: 1.0 lot = 100 oz, so $1 price move = $100 per lot.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

USD_PER_LOT_PER_DOLLAR = 100.0  # 1 lot = 100 oz


@dataclass
class CostModel:
    spread: float = 0.30          # $ per oz round-turn (bid/ask)
    commission_per_lot: float = 7.0  # $ per lot round-turn
    name: str = "realistic"


COST_SCENARIOS = {
    "ideal": CostModel(spread=0.0, commission_per_lot=0.0, name="ideal"),
    "realistic": CostModel(spread=0.30, commission_per_lot=7.0, name="realistic"),
    "pessimistic": CostModel(spread=0.50, commission_per_lot=10.0, name="pessimistic"),
}


@dataclass
class Trade:
    direction: int
    entry_time: pd.Timestamp
    entry: float
    stop: float
    target: float
    lots: float
    exit_time: pd.Timestamp = None
    exit: float = None
    pnl: float = 0.0
    r_multiple: float = 0.0
    reason: str = ""
    bars_held: int = 0
    conf: int = 0   # 1 = sure setup, 0 = unsure


@dataclass
class BacktestResult:
    trades: list = field(default_factory=list)
    equity_curve: pd.Series = None
    start_equity: float = 0.0
    end_equity: float = 0.0
    strategy: str = ""
    tf: str = ""
    cost: str = ""


def run(
    df: pd.DataFrame,
    signals: pd.DataFrame,
    start_equity: float = 10_000.0,
    risk_pct: float = 0.01,
    cost: CostModel | None = None,
    atr_series: pd.Series | None = None,
    atr_trail_mult: float | None = None,
    max_bars: int | None = None,
    min_lot: float = 0.01,
    lot_step: float = 0.01,
    leverage: float = 100.0,
    enforce_margin: bool = False,
    ruin_stop: bool = False,
    adaptive_fn=None,
) -> BacktestResult:
    if cost is None:
        cost = COST_SCENARIOS["realistic"]

    idx = df.index
    o = df["Open"].values
    h = df["High"].values
    l = df["Low"].values
    c = df["Close"].values

    sdir = signals["dir"].fillna(0).values.astype(int)
    sstop = signals["stop"].values
    starget = signals["target"].values
    sconf = signals["conf"].fillna(0).values.astype(int) if "conf" in signals else np.zeros(len(df), int)
    sexit = signals["exit"].fillna(False).values.astype(bool) if "exit" in signals else np.zeros(len(df), bool)
    atr_vals = atr_series.values if atr_series is not None else None

    equity = start_equity
    eq_curve = np.full(len(df), np.nan)

    trades: list[Trade] = []
    pos: Trade | None = None
    trail_stop = np.nan

    def round_lots(x: float) -> float:
        steps = np.floor(x / lot_step)
        return max(min_lot, steps * lot_step)

    for i in range(len(df)):
        # ---- manage an open position on bar i ----
        if pos is not None:
            exit_price = None
            reason = ""

            # 1) intrabar stop / target (stop priority)
            cur_stop = trail_stop if not np.isnan(trail_stop) else pos.stop
            if pos.direction == 1:
                if l[i] <= cur_stop:
                    exit_price, reason = cur_stop, "stop"
                elif not np.isnan(pos.target) and h[i] >= pos.target:
                    exit_price, reason = pos.target, "target"
            else:
                if h[i] >= cur_stop:
                    exit_price, reason = cur_stop, "stop"
                elif not np.isnan(pos.target) and l[i] <= pos.target:
                    exit_price, reason = pos.target, "target"

            # 2) signal-based exit (decided previous close) -> exit at this open
            if exit_price is None and i > 0 and sexit[i - 1]:
                exit_price, reason = o[i], "signal"

            # 3) time stop
            if exit_price is None and max_bars is not None and pos.bars_held >= max_bars:
                exit_price, reason = o[i], "time"

            if exit_price is not None:
                gross = (exit_price - pos.entry) * pos.direction * pos.lots * USD_PER_LOT_PER_DOLLAR
                fees = cost.spread * pos.lots * USD_PER_LOT_PER_DOLLAR + cost.commission_per_lot * pos.lots
                pnl = gross - fees
                risk_dollars = abs(pos.entry - pos.stop) * pos.lots * USD_PER_LOT_PER_DOLLAR
                pos.exit_time = idx[i]
                pos.exit = exit_price
                pos.pnl = pnl
                pos.r_multiple = pnl / risk_dollars if risk_dollars > 0 else 0.0
                pos.reason = reason
                equity += pnl
                trades.append(pos)
                pos = None
                trail_stop = np.nan
            else:
                pos.bars_held += 1
                # update ATR trailing stop
                if atr_trail_mult is not None and atr_vals is not None and not np.isnan(atr_vals[i]):
                    if pos.direction == 1:
                        new_ts = h[i] - atr_trail_mult * atr_vals[i]
                        trail_stop = new_ts if np.isnan(trail_stop) else max(trail_stop, new_ts)
                    else:
                        new_ts = l[i] + atr_trail_mult * atr_vals[i]
                        trail_stop = new_ts if np.isnan(trail_stop) else min(trail_stop, new_ts)

        # ---- ruin: stop trading if account is wiped ----
        if ruin_stop and equity <= 0:
            eq_curve[i] = equity
            continue

        # ---- consider a new entry on bar i (decided at bar i-1 close) ----
        if pos is None and i > 0 and sdir[i - 1] != 0:
            direction = sdir[i - 1]
            entry = o[i]
            stop = sstop[i - 1]
            target = starget[i - 1]
            stop_dist = abs(entry - stop)
            conf = sconf[i - 1]
            allow = True
            if adaptive_fn is not None:
                allow = adaptive_fn(trades, conf, direction, idx[i])
            if stop_dist > 0 and not np.isnan(stop) and allow:
                risk_dollars = equity * risk_pct
                lots = round_lots(risk_dollars / (stop_dist * USD_PER_LOT_PER_DOLLAR))
                # margin required to open 0.01-lot+ at this price
                margin_needed = entry * lots * USD_PER_LOT_PER_DOLLAR / leverage
                can_open = (not enforce_margin) or (equity >= margin_needed)
                if lots > 0 and can_open:
                    pos = Trade(
                        direction=direction, entry_time=idx[i], entry=entry,
                        stop=stop, target=target, lots=lots, conf=conf,
                    )

        eq_curve[i] = equity

    res = BacktestResult(
        trades=trades,
        equity_curve=pd.Series(eq_curve, index=idx).ffill(),
        start_equity=start_equity,
        end_equity=equity,
        cost=cost.name,
    )
    return res

"""
analyze_account.py — can a small account (e.g. $20) trade gold, and does a
%-of-equity (compounding) model grow it?

Two parts:
  1) Static feasibility: margin to open the minimum 0.01 lot, and the dollar risk
     of a typical stop at the 0.01-lot floor, vs account size.
  2) Live simulation: run the best lower-TF strategies from several starting
     balances over the recent era (2019-2026), risking 1% of *current* equity
     (compounding), with margin + ruin enforced.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import data_loader, engine
from strategies import breakout_retest, ema_williams

USD_PER_LOT_PER_DOLLAR = 100.0  # 1 lot = 100 oz
MIN_LOT = 0.01
LEVERAGE = 100.0

# representative 2.5*ATR stop sizes (today's gold, from measured median ATR)
TYPICAL_STOP = {"15m": 12.0, "30m": 18.0, "1h": 25.0, "4h": 50.0, "1d": 110.0}


def static_table():
    print("=" * 78)
    print("PART 1 — Minimum 0.01-lot reality at today's gold prices (1:100 leverage)")
    print("=" * 78)
    print("\n0.01 lot = 1 oz. Margin to OPEN = price / 100. Risk at 0.01 lot = stop$ x 1.\n")
    print(f"{'Gold price':>11} | {'Margin to open 0.01':>20} | {'1h stop $25 risk':>16} | {'4h stop $50 risk':>16}")
    print("-" * 74)
    for px in [1500, 2000, 3000, 4000, 5000]:
        margin = px / LEVERAGE
        print(f"{px:>10} | {margin:>19.2f} | {25.0:>15.2f} | {50.0:>15.2f}")

    print("\nWhat that 0.01-lot risk is as a % of the account (1h stop ~ $25):")
    print(f"{'Account':>9} | {'margin ok? (gold $3000)':>23} | {'risk % per trade (1h)':>22} | {'risk % per trade (4h $50)':>26}")
    print("-" * 88)
    for acct in [20, 50, 100, 200, 500, 1000, 2000, 5000]:
        margin_ok = "YES" if acct >= 3000 / LEVERAGE else "NO (can't open!)"
        r1 = 25.0 / acct * 100
        r4 = 50.0 / acct * 100
        print(f"{acct:>8} | {margin_ok:>23} | {r1:>21.1f}% | {r4:>25.1f}%")


def reconstruct(res, start):
    """Per-trade effective risk% off running equity."""
    eq = start
    effs = []
    for t in res.trades:
        risk = abs(t.entry - t.stop) * t.lots * USD_PER_LOT_PER_DOLLAR
        effs.append(risk / eq * 100 if eq > 0 else np.nan)
        eq += t.pnl
    return np.nanmedian(effs) if effs else np.nan


def sim(gen, name, tf):
    df = data_loader.load(tf)
    df = df[df.index >= "2019-01-01"]        # recent era = realistic for a new account
    out = gen(df, tf)
    cost = engine.COST_SCENARIOS["realistic"]
    print(f"\n{name} [{tf}] — start 2019, risk 1%/trade (compounding), margin+ruin enforced")
    print(f"{'Start $':>8} | {'End $':>12} | {'Min equity':>10} | {'Busted?':>8} | {'Trades taken':>12} | {'Eff risk/trade':>14}")
    print("-" * 80)
    for start in [20, 50, 100, 200, 500, 1000, 2000, 5000]:
        res = engine.run(df, out["signals"], start_equity=start, risk_pct=0.01, cost=cost,
                         atr_series=out.get("atr_series"), atr_trail_mult=out.get("atr_trail_mult"),
                         max_bars=out.get("max_bars"),
                         enforce_margin=True, ruin_stop=True)
        eq = res.equity_curve
        min_eq = eq.min()
        busted = "YES" if min_eq <= 0 or res.end_equity <= start * 0.1 else "no"
        eff = reconstruct(res, start)
        print(f"{start:>8} | {res.end_equity:>12,.0f} | {min_eq:>10,.1f} | {busted:>8} | "
              f"{len(res.trades):>12} | {eff:>13.1f}%")


if __name__ == "__main__":
    static_table()
    print("\n" + "=" * 78)
    print("PART 2 — Compounding simulation from different starting balances (2019-2026)")
    print("=" * 78)
    sim(breakout_retest.generate, "breakout_retest", "1h")
    sim(ema_williams.generate, "ema_williams", "1h")
    sim(breakout_retest.generate, "breakout_retest", "4h")

"""
run_backtest.py — run the full strategy x timeframe x cost matrix and write results.

Outputs (in results/):
    all_results.csv          every (strategy, tf, period, cost) row with metrics
    summary.md               formatted comparison + winner recommendation
    equity_<strat>_<tf>.png  equity curve (best TF per strategy, realistic cost, full period)
    trades_<strat>_<tf>.csv  trade log (realistic cost, full period)
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import data_loader
import engine
import metrics as M
from strategies import REGISTRY

warnings.filterwarnings("ignore")
RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)

START_EQUITY = 10_000.0
RISK_PCT = 0.01

PERIODS = {
    "full": (None, None),
    "IS_2004_2018": (None, "2018-12-31"),
    "OOS_2019_2026": ("2019-01-01", None),
}


def slice_period(df, start, end):
    if start is not None:
        df = df[df.index >= start]
    if end is not None:
        df = df[df.index <= end]
    return df


def buy_hold(df, tf, period_name) -> dict:
    if len(df) < 2:
        return None
    eq = START_EQUITY * (df["Close"] / df["Close"].iloc[0])
    running_max = eq.cummax()
    dd = ((eq - running_max) / running_max).min() * 100
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    end_eq = float(eq.iloc[-1])
    cagr = ((end_eq / START_EQUITY) ** (1 / years) - 1) * 100 if years > 0 else 0.0
    return {
        "strategy": "buy_hold", "tf": tf, "period": period_name, "cost": "ideal",
        "trades": 1, "win_rate": 100.0 if end_eq > START_EQUITY else 0.0,
        "profit_factor": np.nan, "expectancy_R": np.nan,
        "total_return_pct": round((end_eq / START_EQUITY - 1) * 100, 1),
        "cagr_pct": round(cagr, 1), "max_dd_pct": round(dd, 1),
        "mar": round(cagr / abs(dd), 2) if dd != 0 else 0.0, "sharpe": np.nan,
        "avg_R": np.nan, "best_R": np.nan, "worst_R": np.nan,
        "max_loss_streak": 0, "avg_bars": len(df), "end_equity": round(end_eq, 0),
    }


def run_all() -> pd.DataFrame:
    rows = []
    equity_for_plot = {}   # (strategy, tf) -> equity series (realistic, full)

    # cache loaded TFs
    loaded = {}

    def get_df(tf):
        if tf not in loaded:
            loaded[tf] = data_loader.load(tf)
        return loaded[tf]

    for name, (gen, tfs) in REGISTRY.items():
        for tf in tfs:
            df_full = get_df(tf)
            for period_name, (ps, pe) in PERIODS.items():
                df = slice_period(df_full, ps, pe)
                if len(df) < 250:
                    continue
                out = gen(df, tf)
                sig = out["signals"]
                for cost_name, cost in engine.COST_SCENARIOS.items():
                    res = engine.run(
                        df, sig,
                        start_equity=START_EQUITY, risk_pct=RISK_PCT, cost=cost,
                        atr_series=out.get("atr_series"),
                        atr_trail_mult=out.get("atr_trail_mult"),
                        max_bars=out.get("max_bars"),
                    )
                    m = M.compute(res, tf)
                    m.update({"strategy": name, "tf": tf, "period": period_name, "cost": cost_name})
                    rows.append(m)

                    if period_name == "full" and cost_name == "realistic":
                        equity_for_plot[(name, tf)] = res.equity_curve
                        M.trades_to_df(res).to_csv(
                            RESULTS / f"trades_{name}_{tf}.csv", index=False)
            print(f"  done: {name} [{tf}]")

    # buy & hold benchmark (per period, on D1)
    for period_name, (ps, pe) in PERIODS.items():
        df = slice_period(get_df("1d"), ps, pe)
        bh = buy_hold(df, "1d", period_name)
        if bh:
            rows.append(bh)

    df_res = pd.DataFrame(rows)
    cols = ["strategy", "tf", "period", "cost", "trades", "win_rate", "profit_factor",
            "expectancy_R", "avg_R", "total_return_pct", "cagr_pct", "max_dd_pct", "mar",
            "sharpe", "max_loss_streak", "best_R", "worst_R", "avg_bars", "end_equity"]
    df_res = df_res[cols]
    df_res.to_csv(RESULTS / "all_results.csv", index=False)

    plot_equities(equity_for_plot, df_res)
    return df_res


def plot_equities(equity_map, df_res):
    # best TF per strategy by full/realistic total return
    fr = df_res[(df_res["period"] == "full") & (df_res["cost"] == "realistic")]
    if fr.empty:
        return
    best = fr.sort_values("total_return_pct", ascending=False).drop_duplicates("strategy")
    for _, r in best.iterrows():
        key = (r["strategy"], r["tf"])
        if key not in equity_map:
            continue
        eq = equity_map[key]
        plt.figure(figsize=(10, 4))
        plt.plot(eq.index, eq.values, lw=1)
        plt.title(f"{r['strategy']} [{r['tf']}] — equity (realistic costs, full period)")
        plt.ylabel("Equity ($)")
        plt.yscale("log")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(RESULTS / f"equity_{r['strategy']}_{r['tf']}.png", dpi=110)
        plt.close()


if __name__ == "__main__":
    print("Running backtest matrix...")
    df = run_all()
    print("\n=== FULL period, realistic costs ===")
    view = df[(df["period"] == "full") & (df["cost"] == "realistic")]
    view = view.sort_values("total_return_pct", ascending=False)
    print(view[["strategy", "tf", "trades", "win_rate", "profit_factor",
                "expectancy_R", "total_return_pct", "cagr_pct", "max_dd_pct"]].to_string(index=False))
    print("\nResults written to results/")

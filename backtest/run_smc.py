"""run_smc.py — full evaluation of the SMC strategy across TFs, periods, costs."""
from __future__ import annotations
import warnings
from pathlib import Path
import pandas as pd

import data_loader, engine, metrics as M
from strategies import smc

warnings.filterwarnings("ignore")
RESULTS = Path(__file__).resolve().parent / "results"

TFS = ["15m", "30m", "1h", "4h"]
PERIODS = {"full": (None, None), "IS": (None, "2018-12-31"), "OOS": ("2019-01-01", None)}


def slice_period(df, s, e):
    if s: df = df[df.index >= s]
    if e: df = df[df.index <= e]
    return df


def run():
    rows = []
    for tf in TFS:
        full = data_loader.load(tf)
        for pname, (ps, pe) in PERIODS.items():
            df = slice_period(full, ps, pe)
            out = smc.generate(df, tf)
            costs = ["ideal", "realistic", "pessimistic"] if pname == "full" else ["realistic"]
            for cname in costs:
                res = engine.run(df, out["signals"], cost=engine.COST_SCENARIOS[cname],
                                 max_bars=out.get("max_bars"))
                m = M.compute(res, tf)
                m.update({"strategy": "smc", "tf": tf, "period": pname, "cost": cname})
                rows.append(m)
                if pname == "full" and cname == "realistic":
                    M.trades_to_df(res).to_csv(RESULTS / f"trades_smc_{tf}.csv", index=False)
        print(f"  done smc [{tf}]")
    df = pd.DataFrame(rows)
    cols = ["strategy","tf","period","cost","trades","win_rate","profit_factor",
            "expectancy_R","total_return_pct","cagr_pct","max_dd_pct","mar","max_loss_streak"]
    df[cols].to_csv(RESULTS / "smc_results.csv", index=False)
    return df[cols]


if __name__ == "__main__":
    print("Running SMC matrix...")
    df = run()
    print("\n=== SMC FULL / realistic ===")
    print(df[(df.period=="full")&(df.cost=="realistic")].to_string(index=False))
    print("\n=== SMC IS vs OOS (realistic) ===")
    io = df[df.period.isin(["IS","OOS"])]
    print(io.pivot_table(index="tf", columns="period",
          values=["expectancy_R","profit_factor","total_return_pct"]).round(2).to_string())
    print("\n=== SMC cost sensitivity (full) ===")
    print(df[df.period=="full"][["tf","cost","total_return_pct","profit_factor","max_dd_pct","mar"]].to_string(index=False))

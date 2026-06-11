"""
run_lowtf.py — focused test of all strategies on 15m / 30m / 1h.
Realistic costs, full + in-sample + out-of-sample. Plus cost sensitivity on the leaders.
"""
from __future__ import annotations
import warnings
from pathlib import Path
import pandas as pd

import data_loader, engine, metrics as M
from strategies import ema_williams, pullback, donchian, ma_cross, breakout_retest

warnings.filterwarnings("ignore")
RESULTS = Path(__file__).resolve().parent / "results"

STRATS = {
    "ema_williams": ema_williams.generate,
    "pullback": pullback.generate,
    "donchian": donchian.generate,
    "ma_cross": ma_cross.generate,
    "breakout_retest": breakout_retest.generate,
}
TFS = ["15m", "30m", "1h"]
PERIODS = {"full": (None, None), "IS": (None, "2018-12-31"), "OOS": ("2019-01-01", None)}


def slice_period(df, s, e):
    if s: df = df[df.index >= s]
    if e: df = df[df.index <= e]
    return df


def run():
    loaded = {tf: data_loader.load(tf) for tf in TFS}
    rows = []
    for name, gen in STRATS.items():
        for tf in TFS:
            for pname, (ps, pe) in PERIODS.items():
                df = slice_period(loaded[tf], ps, pe)
                out = gen(df, tf)
                for cname in (["ideal", "realistic", "pessimistic"] if pname == "full" else ["realistic"]):
                    cost = engine.COST_SCENARIOS[cname]
                    res = engine.run(df, out["signals"], cost=cost,
                                     atr_series=out.get("atr_series"),
                                     atr_trail_mult=out.get("atr_trail_mult"),
                                     max_bars=out.get("max_bars"))
                    m = M.compute(res, tf)
                    m.update({"strategy": name, "tf": tf, "period": pname, "cost": cname})
                    rows.append(m)
            print(f"  done {name} [{tf}]")
    df = pd.DataFrame(rows)
    cols = ["strategy","tf","period","cost","trades","win_rate","profit_factor",
            "expectancy_R","total_return_pct","cagr_pct","max_dd_pct","mar","max_loss_streak"]
    df = df[cols]
    df.to_csv(RESULTS / "lowtf_results.csv", index=False)
    return df


if __name__ == "__main__":
    print("Running lower-TF matrix (15m/30m/1h)...")
    df = run()
    print("\n=== FULL / realistic, ranked by MAR ===")
    fr = df[(df.period=="full")&(df.cost=="realistic")].sort_values("mar", ascending=False)
    print(fr[["strategy","tf","trades","win_rate","profit_factor","expectancy_R",
              "total_return_pct","max_dd_pct","mar","max_loss_streak"]].to_string(index=False))
    print("\n=== IS vs OOS expectancy (realistic) ===")
    io = df[df.period.isin(["IS","OOS"])]
    piv = io.pivot_table(index=["strategy","tf"], columns="period",
                         values=["expectancy_R","profit_factor"])
    print(piv.round(2).to_string())

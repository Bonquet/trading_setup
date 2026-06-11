"""
analyze_monthly.py — test market filters + reduced SL/TP, judged by MONTHLY returns
(consistency), which is the real goal. Also compares H1 vs H4 vs D1.
"""
from __future__ import annotations
import numpy as np, pandas as pd
import data_loader, engine, metrics as M, indicators as ind
from strategies import combo_small


def feature_frame(df, tf):
    adx_, pdi, mdi = ind.adx(df, 14)
    f = pd.DataFrame(index=df.index)
    f["adx"] = adx_
    f["hour"] = df.index.hour
    htf_name = {"1h": "4h", "30m": "4h", "15m": "4h", "4h": "1d"}.get(tf, "1d")
    htf_h = {"4h": 4, "1d": 24}[htf_name]
    htf = data_loader.load(htf_name)
    tr = pd.Series(ind.market_structure(htf)["trend"], index=htf.index)
    tr.index = tr.index + pd.Timedelta(hours=htf_h)
    f["htf"] = tr.reindex(f.index.union(tr.index)).sort_index().ffill().reindex(f.index)
    return f


def apply_mask(sig, keep):
    s = sig.copy()
    drop = (s["dir"] != 0) & (~keep)
    s.loc[drop, "dir"] = 0
    s.loc[drop, "stop"] = np.nan
    s.loc[drop, "target"] = np.nan
    return s


def monthly_stats(res):
    eq = res.equity_curve
    m = eq.resample("ME").last()
    r = m.pct_change().dropna() * 100
    if len(r) == 0:
        return None
    return {
        "months": len(r),
        "avg_%": round(r.mean(), 2),
        "median_%": round(r.median(), 2),
        "pos_months_%": round(100 * (r > 0).mean(), 1),
        "worst_%": round(r.min(), 2),
        "best_%": round(r.max(), 2),
    }


def run(df, tf, label, keep=None, rr=2.0, stop_max=15):
    out = combo_small.generate(df, tf, stop_atr=2.0, stop_max=stop_max, rr=rr)
    sig = out["signals"] if keep is None else apply_mask(out["signals"], keep)
    res = engine.run(df, sig, cost=engine.COST_SCENARIOS["realistic"], max_bars=out.get("max_bars"))
    m = M.compute(res, tf)
    ms = monthly_stats(res)
    print(f"{label:>30} | trades {m['trades']:>4} | win% {m['win_rate']:>4} | expR {m['expectancy_R']:>6} | "
          f"ret% {m['total_return_pct']:>6} | DD% {m['max_dd_pct']:>6} || mo: avg {ms['avg_%']:>5}% | +mo {ms['pos_months_%']:>4}% | worst {ms['worst_%']:>6}%")


print("H1 — filters & reduced SL/TP (1% risk; monthly stats on right)\n")
df = data_loader.load("1h")
f = feature_frame(df, "1h")
base = combo_small.generate(df, "1h", stop_atr=2.0, stop_max=15)["signals"]
dirn = base["dir"]
agree = ((dirn == 1) & (f["htf"] == 1)) | ((dirn == -1) & (f["htf"] == -1))
no_london = ~f["hour"].between(7, 11)
adx_ok = f["adx"] >= 20
adx_strong = f["adx"] >= 25

run(df, "1h", "baseline (stop15 RR2)")
run(df, "1h", "+ H4 agreement", keep=agree)
run(df, "1h", "+ avoid London", keep=no_london)
run(df, "1h", "+ ADX>=20", keep=adx_ok)
run(df, "1h", "+ ADX>=25", keep=adx_strong)
run(df, "1h", "H4agree+noLondon+ADX20", keep=agree & no_london & adx_ok)
print()
print("Reduce BOTH SL & TP (tighter), with the combined filter:")
combo_keep = agree & no_london & adx_ok
run(df, "1h", "RR2 stop12 +filter", keep=combo_keep, rr=2.0, stop_max=12)
run(df, "1h", "RR1.5 stop12 +filter", keep=combo_keep, rr=1.5, stop_max=12)
run(df, "1h", "RR1.5 stop10 +filter", keep=combo_keep, rr=1.5, stop_max=10)
run(df, "1h", "RR1.2 stop10 +filter", keep=combo_keep, rr=1.2, stop_max=10)
print()
print("Higher timeframes for comparison (monthly consistency):")
for tf in ["4h", "1d"]:
    d = data_loader.load(tf)
    run(d, tf, f"{tf} baseline RR2", stop_max=25 if tf=="4h" else 0)

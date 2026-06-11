"""
analyze_losses.py — WHY do trades lose? Tag each trade with market conditions at
entry, compare winners vs losers, and find filters that avoid the bad trades.
Then report MONTHLY returns (what actually matters for the goal).
"""
from __future__ import annotations
import numpy as np, pandas as pd
import data_loader, engine, metrics as M, indicators as ind
from strategies import combo_small

TF = "1h"
df = data_loader.load(TF)

# feature frame at each bar
adx_, pdi, mdi = ind.adx(df, 14)
ema_f = ind.ema(df["Close"], 50); ema_s = ind.ema(df["Close"], 200)
atr_ = ind.atr(df, 14)
feat = pd.DataFrame(index=df.index)
feat["adx"] = adx_
feat["ema_sep_pct"] = (ema_f - ema_s).abs() / df["Close"] * 100
feat["atr_pct"] = atr_ / df["Close"] * 100
feat["hour"] = df.index.hour
feat["dow"] = df.index.dayofweek

# 4H higher-TF trend agreement (no look-ahead)
h4 = data_loader.load("4h")
h4_trend = pd.Series(ind.market_structure(h4)["trend"], index=h4.index)
h4_trend.index = h4_trend.index + pd.Timedelta(hours=4)
feat["h4_trend"] = h4_trend.reindex(feat.index.union(h4_trend.index)).sort_index().ffill().reindex(feat.index)


def get_trades(stop_max=15, **kw):
    out = combo_small.generate(df, TF, stop_atr=2.0, stop_max=stop_max, **kw)
    res = engine.run(df, out["signals"], cost=engine.COST_SCENARIOS["realistic"], max_bars=out.get("max_bars"))
    return res


res = get_trades()
rows = []
for t in res.trades:
    if t.entry_time not in feat.index:
        continue
    f = feat.loc[t.entry_time]
    agree = (t.direction == 1 and f["h4_trend"] == 1) or (t.direction == -1 and f["h4_trend"] == -1)
    rows.append({"win": t.pnl > 0, "R": t.r_multiple, "dir": t.direction,
                 "adx": f["adx"], "ema_sep": f["ema_sep_pct"], "atr_pct": f["atr_pct"],
                 "hour": f["hour"], "dow": f["dow"], "h4_agree": agree, "reason": t.reason})
T = pd.DataFrame(rows)
print(f"Total trades: {len(T)} | win rate {100*T['win'].mean():.1f}% | expectancy {T['R'].mean():.3f}R\n")

print("=== Winners vs Losers: average conditions at entry ===")
print(T.groupby("win")[["adx", "ema_sep", "atr_pct"]].mean().round(2).to_string())
print()
print("=== Win rate by ADX bucket (trend strength) ===")
T["adx_bucket"] = pd.cut(T["adx"], [0, 15, 20, 25, 30, 100])
print(T.groupby("adx_bucket", observed=True).agg(n=("win", "size"), winrate=("win", lambda x: round(100*x.mean(), 1)), expR=("R", lambda x: round(x.mean(), 3))).to_string())
print()
print("=== Win rate by H4 higher-TF agreement ===")
print(T.groupby("h4_agree").agg(n=("win","size"), winrate=("win", lambda x: round(100*x.mean(),1)), expR=("R", lambda x: round(x.mean(),3))).to_string())
print()
print("=== Win rate by exit reason ===")
print(T.groupby("reason").agg(n=("win","size"), winrate=("win", lambda x: round(100*x.mean(),1)), expR=("R", lambda x: round(x.mean(),3))).to_string())
print()
print("=== Win rate by session (hour, UTC) ===")
T["session"] = pd.cut(T["hour"], [-1,6,11,16,23], labels=["Asia(0-6)","London(7-11)","NY(12-16)","Late(17-23)"])
print(T.groupby("session", observed=True).agg(n=("win","size"), winrate=("win", lambda x: round(100*x.mean(),1)), expR=("R", lambda x: round(x.mean(),3))).to_string())

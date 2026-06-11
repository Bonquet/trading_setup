# XAUUSD Strategy Backtest — Findings & Best Strategy

**Data:** 22 years of gold, 2004-06 → 2026-01, all timeframes (your `XAU_*_data.csv`).
**Engine:** event-driven, no look-ahead (entry on next bar's open), 1% risk/trade, $10k start.
**Tested:** 6 strategies × multiple timeframes × 3 cost scenarios × 3 periods (full / 2004-18 in-sample / 2019-26 out-of-sample).
**Costs modeled:** ideal ($0), realistic ($0.30 spread + $7/lot), pessimistic ($0.50 + $10/lot).

---

## TL;DR — The answer

1. **Your scalper bot loses because it fights gold's nature.** Gold's edge is multi-week/month *trend persistence*; M5 scalping with sub-1R targets and disabled spread filters pays the spread to harvest noise that isn't there.
2. **The winning approach is higher-timeframe trend & breakout trading (4H–Daily).** The *same* strategy logic flips from losing on 1H to winning on Daily — timeframe is the deciding factor for gold.
3. **"Longest possible" is NOT best.** Weekly/Monthly mechanical trend timing *failed* out-of-sample. The sweet spot is **4H–D1**, not W1/Monthly.
4. **Best overall strategy: 50/200 EMA trend-follow on 4H** (most robust, cost-insensitive, smallest drawdown per unit return). **Co-winner: your own playbook's 50 EMA Williams on Daily** — it genuinely works, just on D1, not M5.

---

## Ranked results — full period, realistic costs (by MAR = CAGR ÷ max drawdown)

| Strategy | TF | Trades | Win% | Profit Factor | Expectancy (R) | Return | Max DD | MAR |
|---|---|---|---|---|---|---|---|---|
| **ma_cross** | **4H** | 198 | 40.4 | **1.67** | **0.265** | +59.6% | **-6.1%** | **0.36** |
| **breakout_retest** | **1D** | 220 | 44.5 | 1.62 | 0.284 | +81.7% | -9.1% | 0.31 |
| **ema_williams** | **1D** | 104 | **54.8** | **1.82** | **0.307** | +30.9% | **-4.3%** | 0.29 |
| breakout_retest | 4H | 1134 | 39.6 | 1.15 | 0.107 | +185.4% | -19.3% | 0.26 |
| ema_williams | 1H | 2495 | 43.7 | 1.09 | 0.048 | +168.1% | -26.7% | 0.17 |
| ema_williams | 4H | 651 | 44.9 | 1.16 | 0.096 | +68.2% | -14.8% | 0.16 |
| donchian | 1W | 163 | 74.8 | 1.62 | 0.108 | +25.1% | -9.3% | 0.11 |
| pullback | 4H | 558 | 40.7 | 1.16 | 0.094 | +60.8% | -20.8% | 0.11 |
| donchian | 1D | 759 | 74.3 | 1.10 | 0.028 | +18.1% | -8.3% | 0.09 |
| pullback | 1D | 98 | 40.8 | 1.33 | 0.127 | +14.5% | -11.3% | 0.06 |
| slow_trend | 1W | 75 | 20.0 | 1.08 | 0.069 | +1.5% | -5.5% | 0.01 |
| ma_cross | 1D | 22 | 40.9 | 1.02 | -0.042 | +0.2% | -3.2% | 0.00 |
| donchian | 4H | 3613 | 69.1 | 0.99 | 0.001 | -11.4% | -42.1% | -0.01 |
| slow_trend | 1M | 37 | 21.6 | 0.87 | 0.061 | -2.8% | -10.8% | -0.01 |
| pullback | 1H | 2152 | 38.4 | 0.95 | -0.020 | -44.5% | -51.0% | -0.05 |

> Returns look "small" because sizing risks only **1% per trade** — that's the point: controlled risk.
> The honest comparison is **risk-adjusted** (Profit Factor, Expectancy, MAR), not raw % vs buy-and-hold.

---

## The two decisive filters (this is what makes the result trustworthy)

### 1. Out-of-sample consistency (must be positive in BOTH halves)
A strategy that only works in the past it was built on is a curve-fit. These held up in **both** 2004-18 and 2019-26:

| Strategy / TF | Expectancy IS → OOS | Profit Factor IS → OOS | Verdict |
|---|---|---|---|
| **ma_cross 4H** | 0.25 → 0.27 | 1.60 → 1.76 | ✅ rock-steady across regimes |
| **breakout_retest 1D** | 0.13 → 0.45 | 1.26 → 1.93 | ✅ positive, improved |
| **ema_williams 1D** | 0.16 → 0.55 | 1.19 → 3.32 | ✅ positive, improved |
| breakout_retest 4H | 0.10 → 0.13 | 1.11 → 1.21 | ✅ positive but thinner |
| donchian 1W | 0.05 → 0.24 | 1.13 → 2.76 | ✅ positive, modest |
| pullback 4H | 0.08 → 0.12 | 1.13 → 1.21 | 🟡 weak but positive |
| ma_cross 1D | 0.26 → **-0.24** | 2.08 → 0.67 | ❌ fails OOS — reject |
| slow_trend 1W | 0.09 → **-0.09** | 1.26 → 0.48 | ❌ fails OOS — reject |
| ema_williams 4H | 0.13 → 0.02 | 1.25 → 0.95 | ❌ decays OOS |
| pullback 1H | ~0 → -0.06 | 0.98 → 0.85 | ❌ negative — reject |

### 2. Cost sensitivity (a real edge barely changes when costs rise)

| Strategy / TF | Return ideal → realistic → pessimistic | MAR ideal → pess |
|---|---|---|
| **ma_cross 4H** | 69% → 60% → 56% | 0.40 → 0.32 (durable) |
| **ema_williams 1D** | 33% → 31% → 30% | 0.35 → 0.28 (durable) |
| **breakout_retest 1D** | 83% → 82% → 73% | 0.31 → 0.27 (durable) |
| breakout_retest 4H | **322% → 185% → 116%** | 0.42 → **0.17 (fragile!)** |

> **breakout_retest 4H is a trap** — its huge headline return is mostly eaten by spread, exactly like the scalper.
> The winners are the ones whose edge is **insensitive to costs**.

---

## Winners

### 🥇 Best overall: `ma_cross` on 4H — 50/200 EMA trend-follow + ATR trailing
- Most **consistent** strategy across both market eras (0.25 → 0.27 expectancy).
- **Cost-insensitive** (edge survives even pessimistic spread).
- Smallest drawdown per unit of return (**MAR 0.36**, max DD only -6%).
- 198 trades over 22 years (~9/year) — enough to trust, calm to run.
- Pure trend-following: long when 50 EMA > 200 EMA, short when below, ATR trailing exit. Aligns perfectly with gold's character.

### 🥇 Co-winner / lowest-risk & most disciplined: `ema_williams` on 1D — *your own playbook strategy*
- Highest **profit factor (1.82)** and **win rate (54.8%)**, **lowest drawdown (-4.3%)** of any tested system.
- Out-of-sample performance **improved** (PF 1.19 → 3.32).
- Only ~5 trades/year — fits your "discipline over frequency" mandate exactly.
- **The key lesson:** your 50 EMA Williams logic is sound. The bot ran it on **M5** (noise). On **Daily** it's a genuine edge.

### 🥉 Best controlled-aggression: `breakout_retest` on 1D
- Best return among the robust group (+82%), PF 1.62, OOS improving, DD -9%.

---

## Answering your specific questions

- **"Is the bot's strategy the best for gold?"** No. It's an M5 scalper; M5/1H systems here are either negative or have huge drawdowns once costs are real. The bot's *ideas* (EMA, pullback, confluence) are fine — the **timeframe and cost handling are wrong**.
- **"Should we use a longer timeframe?"** Yes — **move up to 4H/Daily**. That single change turns losing logic into winning logic. But do **not** go all the way to Weekly/Monthly mechanical timing — that failed out-of-sample (too few signals, whipsaws against gold's secular uptrend).
- **Buy-and-hold context:** gold buy-and-hold returned **+1173%** over the period but with a brutal **-44.6% drawdown** (MAR 0.28). The active strategies make less in raw terms *only because they risk 1%/trade* — but they do it with **5-10× smaller drawdowns**. Scaled to the same risk budget, the top strategies beat buy-and-hold on a risk-adjusted basis while being survivable.

---

## Honest limitations
- Single-position, single-instrument, fixed parameters (no optimization — deliberate, to avoid curve-fitting). Light tuning could improve robust systems further (and should itself be walk-forward validated).
- HTF "bias" is approximated with a same-TF 200-EMA filter rather than a true multi-TF feed (kept simple to avoid look-ahead bugs).
- Costs are modeled as flat spread+commission; real gold spread widens around news (NFP/FOMC/CPI) — a news filter would help live.
- Data is one broker's series; live fills, swaps, and slippage will differ. Treat absolute numbers as directional, the **rankings** as the reliable takeaway.

## Suggested next steps
1. Pick the winner to pursue (recommend **ma_cross 4H** for robustness, or **ema_williams 1D** for lowest-risk/discipline).
2. Walk-forward parameter tuning on the chosen system (small grid, OOS-validated).
3. Add a news/session filter and re-test.
4. Then — and only then — wire the validated logic into a fresh, simple EA (no scalp mode, real spread filter, enforced ≥2R) or run it as signals through your existing session routine.

*Artifacts: `all_results.csv` (every run), `trades_<strategy>_<tf>.csv` (trade logs), `equity_*.png` (curves).*

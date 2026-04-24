# XAUUSD Strategy — 50 EMA Williams + Pullback Confluence

Source PDFs: `50 EMA_copy.pdf` (Nenad Kerkez, Admiral Markets), `Pullback-Trading-Strategy_copy.pdf`. Extracted text in `50_EMA.txt` and `Pullback.txt`.

Primary asset: **XAUUSD (Gold)**. Primary timeframe: **H4** for setup, **H1/M15** for entry refinement, **D1** for bias.

---

## 1. Indicators on Chart

- **50 EMA High** and **50 EMA Low** (two EMAs — one on highs, one on lows; forms a channel)
- **Williams %R** (period 14) — levels -20 and -80
- **Stochastic Oscillator** (default 14,3,3) — levels 40 and 60, with signal line
- **Daily Pivot Points** (PP, R1, R2, S1, S2) — computed from prior day H/L/C
- **Parabolic SAR** (from pullback strategy, confluence)
- **Fibonacci retracement** drawn on the most recent impulsive leg (38.2, 50, 61.8, 78.6)

---

## 2. Trend / Bias (from Pullback doc)

- **Bullish** when price makes higher highs and higher lows, and sits above 50 EMA channel
- **Bearish** when price makes lower highs and lower lows, and sits below 50 EMA channel
- **No-trade** if price is chopping inside the 50 EMA High/Low channel — wait for a clean break

Determine bias on **D1 first**, then confirm on **H4**. Only take setups aligned with D1 bias.

---

## 3. BUY Setup (all conditions must agree)

1. Trend filter: D1 + H4 bullish (HH/HL, price above 50 EMA channel)
2. **Price crosses above the 50 EMA High** on H4 (or pulls back INTO the channel and reclaims the 50 EMA High)
3. **Williams %R crosses above -20** (momentum firing)
4. **Stochastic above its signal line AND above level 60**
5. **Pullback confluence**: price is reacting off a Fibonacci level (38.2 / 50 / 61.8) of the last bullish leg, OR Parabolic SAR dots have flipped below price
6. Entry on the close of the confirmation candle on H4 (or refined trigger on H1/M15 — engulfing, pin bar, or break-and-retest of the 50 EMA)

**Stop Loss:** a few pips below the most recent swing low.
**Take Profit:** minimum 2× the SL distance (2R). Targets prioritized at **daily pivot R1 → R2**. Close half at R1, trail remainder. Alternative exit: close when price closes back below the 50 EMA High.

---

## 4. SELL Setup (all conditions must agree)

1. Trend filter: D1 + H4 bearish (LH/LL, price below 50 EMA channel)
2. **Price crosses below the 50 EMA Low** on H4 (or pulls back up into the channel and rejects the 50 EMA Low)
3. **Williams %R crosses below -80** (momentum firing to the downside)
4. **Stochastic below its signal line AND below level 40**
5. **Pullback confluence**: rejection off a Fibonacci level of the last bearish leg, OR Parabolic SAR dots flipped above price
6. Entry on the close of the confirmation candle on H4 (or refined trigger on H1/M15)

**Stop Loss:** a few pips above the most recent swing high.
**Take Profit:** minimum 2× SL (2R). Targets at **daily pivot S1 → S2**. Half off at S1, trail remainder. Alternative exit: close when price closes back above the 50 EMA Low.

---

## 5. Pivot Point Rules (from 50 EMA doc)

- Go long above the Daily Pivot (DP), short below it — aligned with bias
- R1 and S1 are the primary targets; R2 and S2 are exit zones, not entry zones (market is already extended there)
- The **first** break of DP is the most meaningful; subsequent crosses are weaker

---

## 6. Filters / Skip Conditions

- Skip if D1 and H4 bias disagree
- Skip if price is stuck inside the 50 EMA High/Low channel (chop)
- Skip during major USD high-impact news (NFP, FOMC, CPI) — wait 30 min after release
- Skip if the nearest pivot target is less than 1R away (no room for 2R minimum TP)
- Prefer London (07:00–11:00 UTC) and NY (12:00–16:00 UTC) sessions; avoid late NY and Asia

---

## 7. Risk

- **1% account risk per trade** (default)
- Position size (XAUUSD, lot units): `lot = (account × 0.01) / (SL_pips × pip_value_per_lot)`
  - For XAUUSD on most brokers, 1.00 lot = 100 oz, and 1 pip (0.10 price move) ≈ $10 per lot. Verify with your broker.
- Max 2 concurrent XAUUSD positions
- Stop trading for the day after 2 consecutive losses

---

## 8. Trade Management

- Move SL to breakeven once price hits 1R
- Partial close 50% at first pivot target (R1/S1), trail remainder to structure
- Full exit on the opposite-side 50 EMA reclaim or opposite Williams %R cross

---

## 9. Open Items to Confirm With User

- Exact Williams %R period (default 14 assumed)
- Whether to use 50 EMA on close vs separate High/Low EMAs (the PDF uses both — confirm your broker's "50 EMA High" / "50 EMA Low" indicator is the same)
- Whether entries are on candle close or immediate fill on cross
- Preferred partial-TP split (50/50 assumed)

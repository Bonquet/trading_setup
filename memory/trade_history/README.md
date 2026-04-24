# trade_history/

Every trade idea produced — valid, skipped, invalidated, or missed. One file per trade.

**Filename:** `YYYY-MM-DD_<instrument>_<strategy>_<result>.md`
Example: `2026-04-24_XAUUSD_50ema_win.md`

## Template

```markdown
---
date_utc: 2026-04-24T07:12:00Z
instrument: XAUUSD
timeframe: H4 (entry), D1 (bias)
strategy: 50 EMA Williams   # or "Pullback"
result: win | loss | breakeven | skipped | invalidated | missed
rr_realized: 2.1            # R multiple; 0 if not taken
---

## Trend Bias
- D1: bullish (HH/HL, above 50 EMA channel)
- H4: bullish

## Market Condition
Trending — clean structure, ATR healthy, London session.

## Setup
- Price crossed above H4 50 EMA High at 2345.20
- Williams %R crossed above -20
- Stoch 68, above signal line
- Fib 61.8% of last H4 impulse at 2343 held

## Entry Plan
- Entry: 2346.50 (H4 close above EMA)
- SL: 2338.00 (below swing low, 85 pips)
- TP1: 2363.50 (2R, near R1)
- TP2: 2380.00 (R2)
- Size: 0.12 lots @ 1% risk of $10,000

## Confirmation signals present
[x] 50 EMA cross  [x] Williams %R  [x] Stoch  [x] Pullback confluence  [x] 2R+ room  [x] HTF aligned

## Higher TF context
D1 uptrend intact, PDH broken, no major USD news in window.

## Rule adherence
All rules followed.

## Outcome
TP1 hit at 2363.50. Trailed TP2, exited at 2378 on 50 EMA reclaim exit. +2.0R avg.

## Post-trade summary
Process was clean. Entry timing good. SL placement good. Trailing via EMA exit captured extra — repeat this management method on trending days.
```

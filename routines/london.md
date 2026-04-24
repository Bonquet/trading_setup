# London Session Routine — XAUUSD

**Window:** ~06:00–11:00 UTC (London open 08:00 UK = 07:00/08:00 UTC depending on DST).
**Goal:** enter a brief before London cash open so user has a plan for the first 4 hours.

## Checklist

1. **Fetch data**
   - Run `python scripts/fetch_gold.py` (live spot + D1, H4, H1, M15 candles)
   - Run `python scripts/compute_levels.py` (50 EMA High/Low per TF, ATR, swings, daily pivots)

2. **Confirm bias**
   - D1: last 10 candles — HH/HL (bull) vs LH/LL (bear)? Price vs D1 50 EMA channel?
   - H4: same check. Must agree with D1, else flag "no-trade — bias mismatch"

3. **Mark key levels**
   - Daily Pivot, R1, R2, S1, S2 (from prior UTC day H/L/C)
   - Previous Day High (PDH), Previous Day Low (PDL)
   - **Asia range:** highest high and lowest low of 00:00–06:00 UTC candles
   - 50 EMA High & Low values on H4 and H1
   - Nearest Fibonacci retracement zone (38.2/50/61.8/78.6) on last H4 impulse

4. **Scan for setups** — per `strategy/50ema_pullback.md` rules
   - Any H4 candle closing through the 50 EMA in direction of bias?
   - Williams %R firing (-20 or -80 cross) in direction of bias?
   - Stochastic confirming (>60 bull / <40 bear, relative to signal line)?
   - Pullback confluence (fib level, PSAR flip, or 50 EMA retest)?
   - Room to the next pivot target ≥ 2R from entry?

5. **News filter**
   - Check economic calendar (user supplies) — any red-folder USD/EUR/GBP events in the next 4 hours?
   - If yes, note the time and either skip that window or size down

6. **Produce London brief** per the output contract in `CLAUDE.md`

## Typical London playbook for XAUUSD
- Asia range often breaks on London open — watch for sweep of Asia H or L into a pivot confluence, then reversal
- If D1 is bullish and price retraces to H4 50 EMA High during Asia, expect London to reclaim and continue up
- Avoid chasing — wait for the 50 EMA reclaim + Williams %R cross; don't pre-fire

## Session end
- At ~11:00 UTC or when user says "NY update", rerun fetch and go to `routines/ny.md`

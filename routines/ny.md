# NY Session Routine — XAUUSD

**Window:** ~12:00–17:00 UTC (NY cash open 13:30 UTC, high-vol window 13:00–16:00 UTC).
**Goal:** refresh the London plan with NY data, kill invalid setups, propose new ones.

## Checklist

1. **Re-fetch data**
   - `python scripts/fetch_gold.py`
   - `python scripts/compute_levels.py`

2. **Review London session outcome**
   - Did price hit London setup entries? Hit TP? Hit SL? Invalidated?
   - Update `journal/trades.md` for any closed trades (user confirms fills)
   - Move any open runners to "breakeven / trailing" notes

3. **Update bias**
   - Has H4 structure changed since London? New swing high/low?
   - Still aligned with D1? (D1 bias rarely flips intraday, but confirm)
   - Did Asia/London take out PDH or PDL? (liquidity sweep changes the map)

4. **Update levels**
   - Daily pivots unchanged (recalculated at 00:00 UTC)
   - Add **London range** (06:00–12:00 UTC H/L) to watchlist
   - Nearest untapped pivot target for bias direction

5. **NY setup scan** — per strategy rules
   - Fresh H4 close in bias direction?
   - Williams %R + Stochastic fresh cross on H1?
   - Fib/PSAR/50 EMA retest confluence still valid?
   - Watch for **London range break + retest** — strongest NY setup for XAU
   - Watch for **fakeout of London H or L into pivot** — reversal setup

6. **News filter**
   - NY has most USD red-folder events — check for US CPI, NFP, FOMC, retail sales in your window
   - FOMC days: no new entries 1h before, 30m after

7. **Produce NY update** per output contract

## Typical NY playbook for XAUUSD
- NY often reverses or extends London; don't assume continuation
- Watch the 13:30 UTC candle — real directional commit often comes here
- DXY inverse-correlation: if DXY is breaking up sharply, XAU setups to the downside get priority
- Before 16:00 UTC London close, liquidity thins — tighten or close runners

## Session end
- At ~17:00 UTC, summarize the day's activity to `journal/trades.md` and flag any carry-over swing positions

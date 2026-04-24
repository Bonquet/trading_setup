# mistakes/

Recurring execution errors. One file per mistake type — UPDATE existing files when a mistake repeats, don't create duplicates.

## Examples
- Entering before pullback completion
- Trades in sideways markets
- Forcing "close enough" setups
- Ignoring HTF structure
- Moving stop too early
- Poor RR trades
- Relying on indicators without trend context

## Per-mistake file template
```markdown
---
mistake: entering before pullback completion
occurrences: 3
markets: [XAUUSD, EURUSD]
timeframes: [H1, M15]
rule_that_should_have_prevented: "Entry only after confirmation candle on retracement zone"
corrective_action: "Require explicit rejection candle close before entry; do not anticipate"
---

## Log
- 2026-04-20 XAUUSD H1 — entered at fib 50% on touch, pulled back 30 pips, stopped.
- 2026-04-22 EURUSD M15 — pre-fired on 38.2%, no confirmation candle, stopped.
- 2026-04-24 XAUUSD H1 — chased without waiting for close.
```

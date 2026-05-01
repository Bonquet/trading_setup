---
mistake: opening two near-identical positions on the same setup within minutes
occurrences: 1
markets: [XAUUSD]
timeframes: [swing]
rule_that_should_have_prevented: "Max 2 concurrent trades means two independent setups, not one setup split into two entries at the same price"
corrective_action: "One entry per setup signal. If the setup qualifies, take it once. Check open[] before entering: if a position in the same direction on the same instrument is already open from the same signal, do not add a second."
---

## Log
- 2026-04-28 T1232Z + T1233Z XAUUSD swing — Two SELLs opened 1 minute apart at 4577.03 and 4581.94. Identical D1+H4 below-channel confluence, Williams and Stoch both extreme oversold. Same signal taken twice. Both stopped at SL (price reversed to 4615), each -1.0R. The savings mirror (T1235Z_m) compounded the error: mirrored the duplicate position, -$380.80 on savings account.

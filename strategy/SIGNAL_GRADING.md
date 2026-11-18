# Williams signal grades

Version: `williams_momentum_v1`. Applied at signal creation, after all existing
entry filters pass. The grade labels momentum conditions, not win probability.
It does not alter entry eligibility, stop/target prices, lot sizes or risk.
These three indicators overlap; three checks are not three independent sources
of evidence. The thresholds have not been optimized or validated for returns.

Each extra check earns one point:

| Style | Williams BUY / SELL | Stochastic K BUY / SELL |
|---|---|---|
| Swing | > -10 / < -90 | > 80 / < 20 |
| Intraday | > -12.5 / < -87.5 | > 77.5 / < 22.5 |
| Scalp | > -5 / < -95 | > 90 / < 10 |

The third check is directional Stochastic separation: K - D >= 5 for BUY,
or D - K >= 5 for SELL. The first two thresholds are halfway from each style's
existing trigger to the indicator's extreme. Calculations use unrounded inputs.

- **A:** 0 or 1 extra checks passed.
- **A+:** 2 extra checks passed.
- **S:** all 3 extra checks passed.

The signal JSON and open/closed ledger retain `setup_grade`, `grade_score`
(0–3), `grade_checks` (values, thresholds, operators, pass flags),
`grade_reason`, and `grading_version`. Grades stay fixed after entry.
Mirrored trades inherit the original signal's grade.
Old trades keep their original records and have no retroactive grade.

Initial Telegram signals and every TP/SL alert use the same full signal block,
including grade when recorded and the unique signal reference. The hit notice
appears underneath. Legacy open trades still get the complete block and reference.
Previously notified targets are not resent by this change.

Example using synthetic prices:

```text
XAUUSD SELL @ 4000.00
Grade: A+
SL: 4010.00
TP1: 3990.00
TP2: 3980.00
TP3: 3975.00
Signal: example-signal

TP1 HIT
Hit price: 3990.00
```

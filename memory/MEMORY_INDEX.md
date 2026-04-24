# Memory Index

Load this file at the start of every session. Then read the specific folder(s) relevant to the instrument, strategy, timeframe, and current market condition in play.

## Folders

| Folder | Purpose | Read before... |
|---|---|---|
| [trade_history/](trade_history/) | Every trade idea produced (valid + skipped + invalidated) with full record | every new brief |
| [wins/](wins/) | Winning trades + why they worked + shared traits | pattern-matching a possible setup |
| [losses/](losses/) | Losing trades + why they failed + rule violations | checking if current setup resembles past failures |
| [mistakes/](mistakes/) | Recurring execution errors + corrective actions | every Valid Trade decision — check for replication |
| [high_probability_setups/](high_probability_setups/) | Textbook-clean wins — the gold-standard library | calibrating confidence on strong setups |
| [market_profiles/](market_profiles/) | How each instrument behaves (XAUUSD, EURUSD, etc.) | first analysis of any instrument in a session |
| [timeframe_profiles/](timeframe_profiles/) | Signal quality per TF | picking TF for entry timing |
| [strategy_performance/](strategy_performance/) | Per-strategy running stats | choosing between Pullback vs 50 EMA Williams |
| [market_conditions/](market_conditions/) | Environment quality notes (trending, chop, news, session) | confirming conditions support the setup |
| [risk_management/](risk_management/) | Stop/target/size lessons | validating SL placement and RR logic |

## File naming conventions

- `trade_history/YYYY-MM-DD_<instrument>_<strategy>_<result>.md` — e.g. `2026-04-24_XAUUSD_pullback_win.md`
- `wins/` and `losses/` — same naming, only the ones that closed with a result
- `mistakes/<short_slug>.md` — one file per recurring mistake, updated (not duplicated) when it recurs
- `high_probability_setups/<short_slug>_<instrument>.md` — e.g. `h4_50ema_reclaim_xauusd.md`
- `market_profiles/<instrument>.md` — one file per instrument
- `timeframe_profiles/<tf>.md` — one file per TF
- `strategy_performance/<strategy>.md` — one file per strategy
- `market_conditions/<condition>.md` — one file per condition type
- `risk_management/<topic>.md` — one file per topic (stop_placement, target_selection, sizing, etc.)

## Memory-aware decision rule

For every trade decision, combine:
1. Current chart analysis
2. Core framework (`strategy/playbook.md`)
3. Historical memory of similar trades

Match to winners → confidence may rise. Match to losers / recurring mistakes → confidence must drop or reject. **Memory never overrides the framework.**

## After every closed trade — update
- `trade_history/` (always)
- `wins/` or `losses/` (result-based)
- `mistakes/` (if rule broken)
- `high_probability_setups/` (if clean textbook)
- Running notes in `strategy_performance/`, `market_profiles/`, `timeframe_profiles/`, `market_conditions/`, `risk_management/`

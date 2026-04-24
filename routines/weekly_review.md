# Weekly Review Routine

Triggered by user saying "weekly review", "week review", or auto-fired by Friday cron at 21:00 UTC.

## Steps

1. Run `python scripts/weekly_stats.py --days 7` and capture the output (also saved to `data/cache/weekly_stats.json`).
2. Read the full `journal/trades.md` entries from the last 7 days.
3. Read `memory/MEMORY_INDEX.md` and scan:
   - `memory/wins/` and `memory/losses/` entries from this week
   - `memory/mistakes/` — any recurring errors?
   - `memory/strategy_performance/` — which system paid this week?
4. Produce a structured review in this exact shape:

### Weekly Review — {week_start} → {week_end} (UTC)

**Stats**
- Ideas / Closed / Pending / Skipped: `{n}/{n}/{n}/{n}`
- W / L / BE: `{n}/{n}/{n}` (win rate `{pct}%`)
- Avg R: `{x}` | Total R: `{x}`

**By strategy**
- 50 EMA Williams: `{n} trades, {w}W/{l}L, {r}R`
- Pullback: `{n} trades, {w}W/{l}L, {r}R`

**What went right**
- Up to 3 bullets — point to specific trades + matching `memory/wins/` entries.

**What went wrong**
- Up to 3 bullets — losses + recurring mistakes. Cite `memory/mistakes/` if pattern repeats.

**Rule adherence**
- Were confirmations required and waited for? (yes/no per trade)
- Any forced trades? Any rule violations?
- Any entries without a matching Memory Review?

**Adjustments for next week**
- Concrete behavioral or filter changes (e.g. "skip trades where Stoch is borderline 55-60").
- New items to add to `memory/mistakes/` or `memory/high_probability_setups/`.

**Memory updates made**
- List every file you wrote/updated in `memory/` during this review.

5. Append the review as a new `## Weekly Review YYYY-MM-DD` section at the top of `journal/trades.md`.
6. Send the short version via WhatsApp: call `scripts/weekly_stats.py --notify` (the script formats + forwards).
7. If any recurring mistake was identified, write/update the corresponding `memory/mistakes/*.md` file.

## Guardrails

- Never fabricate trades or stats — only what's in the journal.
- If the journal is empty for the window, output "No trades this week. Nothing to review." and skip memory updates.
- Never modify `memory/wins/` or `memory/losses/` retroactively during a review — only add new entries.

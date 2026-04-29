# Remote Weekly Review Routine

**Schedule**: Friday 21:30 UTC (30 min after the bot's `/summary` cron, after NY close)
**Runs**: As a remote Claude Code agent in Anthropic's cloud — no PC needed.
**Output**: WhatsApp summary + journal append + memory updates.

This is the **deep narrative review** of the week — beyond the bot's `/summary` numbers. It reads journal entries, cross-references `memory/`, identifies recurring patterns, and writes back to the repo so next week's analysis benefits.

## Steps the agent runs

1. Read `routines/weekly_review.md`, journal, memory folders, accounts state
2. Run `python scripts/weekly_stats.py --days 7` for raw numbers
3. Compose narrative review per the format in `routines/weekly_review.md`:
   - Stats summary
   - By-strategy breakdown
   - What went right (cite specific trades + matching `memory/wins/` files)
   - What went wrong (cite losses + recurring mistakes from `memory/mistakes/`)
   - Rule adherence audit
   - Adjustments for next week
4. Append review as new `## Weekly Review YYYY-MM-DD` section at TOP of `journal/trades.md`
5. Update `memory/`:
   - Per loss: ensure `memory/losses/YYYY-MM-DD_<instrument>_<strategy>.md` exists
   - Per recurring mistake: append to `memory/mistakes/<topic>.md`
   - Per clean win: ensure `memory/wins/...md` exists
6. Send concise WhatsApp summary (≤1500 chars)
7. Commit + push everything

## WhatsApp summary format

```
XAU Weekly Review YYYY-MM-DD → YYYY-MM-DD
Closed: NW/NL/NBE | WR: X% | Total: $Y (ZR)
50EMAW: ... | Pullback: ...

Right: <1 line>
Wrong: <1 line>
Adjust: <1 line>
```

## Editing the prompt

Same as morning routine — update via the `schedule` skill or at https://claude.ai/code/routines

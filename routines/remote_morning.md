# Remote Morning Brief Routine

**Schedule**: 06:30 UTC Mon–Fri (30 minutes before the bot's London cron)
**Runs**: As a remote Claude Code agent in Anthropic's cloud — no PC needed.
**Output**: One WhatsApp message via `scripts/notify_whatsapp.py`.

This routine is the **judgment layer** the mechanical bot can't provide:
- Evaluates BOTH the 50 EMA Williams AND Pullback strategies (bot does only the former)
- Scans for high-impact USD news in the next 24h
- Gives a borderline-aware second opinion before the 07:00 UTC bot cron fires

The remote agent's prompt is set in the scheduled trigger via the `schedule` skill. The version of the prompt below is the canonical source — keep this file and the live trigger prompt in sync.

## Steps the agent runs

1. Read playbook + memory + recent journal + active account
2. Run `fetch_gold.py` + `compute_levels.py`
3. Analyze 50 EMA Williams (deterministic) AND Pullback (judgmental) on current data
4. WebSearch for high-impact USD events in next 24h
5. Compose a structured brief (≤1500 chars to fit one WhatsApp message)
6. Send via `notify_whatsapp.py`
7. Commit any data/cache or memory changes back to repo

## Brief format

```
XAU Morning Brief — YYYY-MM-DD UTC
Spot: $X | D1 [pos] H4 [pos]

50 EMA WILLIAMS:
[Valid Trade / No Trade]
[reason; if valid include entry/SL/TP/lots]

PULLBACK:
[Setup forming / No setup]
[structure description]

NEWS NEXT 24H:
[events + UTC times, or "none flagged"]

ACTION: [hold / wait for X / take Y]
```

## Editing the prompt

To change what the agent does, update the trigger via the `schedule` skill:
- `RemoteTrigger { action: "list" }` to find the trigger ID
- `RemoteTrigger { action: "update", trigger_id: "...", body: { job_config: { ccr: { events: [...] } } } }`

Or edit it in the web UI at https://claude.ai/code/routines

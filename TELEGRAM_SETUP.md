# Telegram Bot Setup

The bot pushes signals/briefs to Telegram **and** accepts commands you send it —
the Telegram equivalent of the WhatsApp setup, but with no 24-hour window and no
manual re-activation. Once you've pressed **Start** on the bot, it can message you
any time, forever.

Bot: **@tradekanashibot** ("Xauusd Bot By Kanashi")
Your chat ID: **5886177468** (already saved in `config/.env`)

## What was added

| File | Purpose |
|------|---------|
| `scripts/notify_telegram.py` | Sends a message to Telegram (one-way push). Used by `run_auto.py` for signals/briefs. `--setup` re-detects your chat ID. |
| `scripts/telegram_poll.py` | Reads commands you send the bot and runs them, replying in-chat. |
| `.github/workflows/telegram-command.yml` | Runs the poller every ~5 min on GitHub Actions (also `workflow_dispatch`). |
| `config/.env` | Holds `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`. |

`accounts.py`, `health_check.py`, `weekly_stats.py` now honour a `NOTIFIER_SCRIPT`
env var so their replies go to Telegram when a command came from Telegram
(default stays `notify_whatsapp.py`, so nothing else changes).

## One manual step: add 2 GitHub repo secrets

GitHub Actions can't read `config/.env` (it's gitignored). Add these as repo secrets:

1. Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**
2. Add:
   - `TELEGRAM_BOT_TOKEN` = (the token from @BotFather — it's in your local `config/.env`)
   - `TELEGRAM_CHAT_ID` = `5886177468`

(If you ever revoke/regenerate the token via @BotFather, update the secret too.)

Then commit & push the new files. The listener workflow starts running on schedule.

## Commands (same set as WhatsApp)

```
/health   /london   /ny   /best [high]   /scalp   /quick   /current   /summary
/accounts /balance  /active /risk /buffer /maxrisk /style
/took     /close    /pnl  /freeze /unfreeze /resetphase   /help
```

## Latency note

GitHub's minimum schedule granularity is 5 minutes (and can lag under load), so a
command you send is picked up within ~5 minutes. For instant response you'd add a
small webhook relay later — but polling needs zero extra infrastructure.

## Security

`telegram_poll.py` only acts on messages from your authorized chat ID
(`TELEGRAM_CHAT_ID`). Anyone else who finds the bot is ignored.

## Going Telegram-only (optional)

WhatsApp still runs in parallel for signals. To silence WhatsApp entirely, set in
`config/.env`:

```
WHATSAPP_BACKEND=disabled
```

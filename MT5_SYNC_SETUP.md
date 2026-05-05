# MT5 Live Sync — Setup Guide

This connects your MetaTrader 5 desktop terminal to the bot using **read-only investor passwords**. The bot then knows your real-time balance, open positions, and closed trades — no more manual `/balance` / `/close` updates.

## What you need

| Requirement | Why |
|---|---|
| Windows PC or Windows VPS | The `MetaTrader5` Python package is Windows-only |
| MT5 desktop terminal installed | The Python package talks to it |
| Python 3.10+ | We already have Python 3.12 set up |
| Investor password for each MT5 account | Read-only credential — cannot place trades, cannot withdraw |

**Investor passwords are safer than master passwords.** Even if leaked, no one can move money or trade. Find them in MT5: **Tools → Options → Server → Change Password → check "Change investor (read-only) password"**.

## Step 1 — Install the Python package

Open PowerShell or CMD and run:

```powershell
C:\Users\acebl\AppData\Local\Programs\Python\Python312\python.exe -m pip install MetaTrader5
```

Verify:
```powershell
C:\Users\acebl\AppData\Local\Programs\Python\Python312\python.exe -c "import MetaTrader5; print(MetaTrader5.__version__)"
```
Should print a version number (e.g., `5.0.45`).

## Step 2 — Make sure MT5 desktop is running

Open MT5 terminal and log into ANY account (the sync script will switch as needed). Just having MT5 open in the background is enough.

## Step 3 — Register your first MT5 account with the bot

For each prop firm account you want synced, run the discovery command. You'll need:
- Your MT5 account **login number** (e.g. `1234567`)
- Your **investor password** (NOT the master password)
- Your **server name** (find it in MT5 → File → Login to Trade Account → Server dropdown, e.g. `FTMO-Server`, `ICMarkets-Live10`, `Eightcap-Live4`)
- A short **bot name** for this account (e.g. `main`, `savings`, `phase2`, `funded1`)

```powershell
cd "C:\Users\acebl\Documents\Trading Setup"
C:\Users\acebl\AppData\Local\Programs\Python\Python312\python.exe scripts\mt5_sync.py --discover 1234567 YourInvestorPwd FTMO-Server main
```

The script will:
1. Probe MT5 with your credentials
2. Print the account name, balance, currency it sees
3. Add an `mt5` block to `accounts.json` for that bot account
4. Print the `.env` line you need to add for the password

After it succeeds, **add the printed env var to `config/.env`**, e.g.:
```
MT5_MAIN_INVESTOR_PWD=YourInvestorPwd
```

Repeat for each MT5 account:
```powershell
python scripts\mt5_sync.py --discover 7654321 OtherInvestorPwd FTMO-Server2 savings
python scripts\mt5_sync.py --discover 9999999 ThirdPwd ICMarkets-Live2 funded1
```

Each becomes its own bot account.

## Step 4 — Run a manual sync to verify

```powershell
python scripts\mt5_sync.py
```

You should see something like:
```
[2026-05-01T15:30Z] Syncing 2 MT5 account(s)…
  [main] logging in as 1234567@FTMO-Server…
  [main] balance $4897.15 equity $4920.02 open positions 1
  [savings] logging in as 7654321@FTMO-Server2…
  [savings] balance $9957.85 equity $9957.85 open positions 0
  done. accounts.json updated.
```

Open `data/accounts.json` and verify the balances match your MT5 reality.

## Step 5 — Schedule it to run every 5 minutes (Windows Task Scheduler)

This keeps `accounts.json` fresh while you trade.

### Quick way (PowerShell, one-time):

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Users\acebl\AppData\Local\Programs\Python\Python312\python.exe" -Argument "C:\Users\acebl\Documents\Trading Setup\scripts\mt5_sync.py --commit" -WorkingDirectory "C:\Users\acebl\Documents\Trading Setup"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName "MT5 Sync" -Action $action -Trigger $trigger -Settings $settings -Description "Sync MT5 account state into trading_setup repo"
```

The `--commit` flag also pushes the updated `accounts.json` to GitHub after each sync, so the bot's cron runs always see fresh data.

### Or run continuously in a console (no Task Scheduler):

```powershell
python scripts\mt5_sync.py --watch 300 --commit
```

Leave the console window open. Closes? Sync stops. Use Task Scheduler for production.

## Step 6 — Verify in WhatsApp

Send `/accounts` from your phone. Each MT5 account should now show with its live balance and the new `equity` field. Send `/current` — open positions should match what's actually on your MT5 screen.

## Once sync is live

You stop using these commands manually (sync handles them):
- `/balance` — accounts.json balance is auto-updated
- `/took` — open positions are pulled from MT5 directly
- `/close` — closed trades append automatically

You still use these:
- `/best`, `/scalp`, `/london`, `/ny` — signal generation
- `/health`, `/summary`, `/pnl` — reporting
- `/freeze`, `/unfreeze` — manual safety override
- `/risk`, `/buffer`, `/maxrisk`, `/style` — config

## Troubleshooting

**"mt5.initialize() failed"** — MT5 desktop terminal isn't running. Open it.

**"mt5.login() failed: (-6, ...)"** — wrong server name or wrong password. Server names are case-sensitive (`FTMO-Server` not `ftmo-server`). Investor password is different from master password.

**"MetaTrader5 package not installed"** — run `pip install MetaTrader5` again with the full path to your Python 3.12 exe.

**Sync runs but `accounts.json` doesn't change** — check `last_synced_at` timestamp in the file. If it updates but balance is the same, MT5 is reporting that balance. Compare to MT5 desktop's "Trade" tab.

**`git push` fails with 403** — your local repo's git auth has expired. Run `gh auth refresh` and re-test. The sync still updates `accounts.json` locally even if push fails; it just won't propagate to the cloud bot.

## Multiple MT5 accounts at once

The sync script logs into each account in sequence. If your MT5 desktop is running and showing account A, the script will switch to account B briefly to sync, then back. **Brief account flicker in MT5 is normal during sync.** Takes ~3 seconds per account.

If you actively trade while sync is running, you may see momentary disconnects. Easy fix: install MT5 a second time in a different folder for sync only (don't actively trade in that copy). Or skip Task Scheduler and run sync only when you're not actively in MT5.

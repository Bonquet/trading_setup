# XAU AutoTrader EA — Install & Configure

Auto-executes signals from your bot directly inside MT5. Polls the public repo for fresh signals, opens market orders with the correct lot size for your current balance, then manages the trade (BE at +1R, partial close at +1.5R, trail to TP2).

## What it does

1. **Polls** `https://raw.githubusercontent.com/Bonquet/trading_setup/main/data/signals/latest.json` every 30s
2. **Validates** the signal: fresh (< 30 min), valid trade, allowed style, deduplicated
3. **Sizes** the lot using your CURRENT MT5 balance × Risk_Percent — not the signal's pre-computed lot
4. **Opens** a market order with the signal's SL and TP2
5. **Manages** the position:
   - At **+1R unrealized**: SL moves to break-even (+2 points buffer)
   - At **+1.5R unrealized**: closes 50% of position (locks profit)
   - **After partial**: trails SL by 0.5 × H1 ATR
6. **Limits**: max 1 open position per EA instance, max 5 trades per day (configurable)

Signals only fire when YOUR bot's signal pipeline produces one. The cron runs at 07:00 and 13:00 UTC weekdays, plus any `/best` / `/scalp` you trigger.

## Install (one-time, ~5 minutes)

### 1. Copy the EA file into MT5's Experts folder

In MT5 desktop:
- **File → Open Data Folder** (opens `%APPDATA%\MetaQuotes\Terminal\<id>\`)
- Navigate to `MQL5\Experts\`
- Copy `XAU_AutoTrader.mq5` from this repo into that folder

### 2. Compile

- In MT5 desktop: **Tools → MetaQuotes Language Editor** (or press F4)
- In MetaEditor: open `Experts/XAU_AutoTrader.mq5`
- Press **F7** to compile
- Should report `0 errors, 0 warnings`. If warnings, ignore them — they don't break the build.

### 3. Whitelist the GitHub URL

The EA uses `WebRequest()` to fetch signals. MT5 blocks WebRequest by default for security.

- MT5 desktop: **Tools → Options → Expert Advisors** tab
- Tick **"Allow WebRequest for listed URL"**
- In the URL list, add: `https://raw.githubusercontent.com`
- Click OK

If you skip this, the EA logs: `WebRequest error 4060 — URL not whitelisted`.

### 4. Enable AutoTrading

The big **AutoTrading** button on the MT5 toolbar must be green / pressed. If it's red, the EA can read signals but cannot place orders.

### 5. Attach the EA to a XAUUSD chart

- Open a XAUUSD chart (or whatever your broker calls gold — XAUUSD, GOLD, XAUUSD.r…)
- Navigate to **Navigator → Expert Advisors → XAU_AutoTrader**
- Drag it onto the chart
- A dialog appears with the input parameters (see Configuration below)
- Click **OK**

A smiley face icon in the chart top-right means it's running. A frowny face means AutoTrading is off, or the EA's permissions are blocked.

### 6. Confirm it's polling

In MT5 desktop, open the **Experts** tab at the bottom. You should see:

```
[INIT] XAU AutoTrader live on XAUUSD | risk=1.0% | poll=30s | magic=4040405
[INIT] Signal source: https://raw.githubusercontent.com/Bonquet/...
```

Every 30 seconds it polls — if no fresh signal, it's silent. When a signal arrives:

```
[OPEN] BUY XAUUSD @ 4698.45 SL=4685.20 TP=4724.00 lots=0.05 risk=$66.25 bal=$4945.22 sid=20260507T07003zZ_abc12345
```

## Configuration

When you attach the EA, set these inputs:

### Connection
| Input | Default | Notes |
|---|---|---|
| `Signal_URL` | github raw URL | Don't change unless you forked the repo |
| `Poll_Seconds` | 30 | Lower = faster fills, higher load |
| `Symbol_Override` | empty | If your broker uses `GOLD` or `XAUUSD.r`, set it here |

### Risk
| Input | Default | Notes |
|---|---|---|
| `Risk_Percent` | 1.0 | % of MT5 balance per trade |
| `Max_Risk_USD` | 0 | Hard $ cap — set to your prop firm's daily DD / 10 |
| `Min_Lot` | 0.01 | Don't trade if calculated lot is below |
| `Max_Lot` | 1.00 | Safety cap |
| `Max_Trades_Per_Day` | 5 | Resets at 00:00 UTC |
| `Max_Open_Positions` | 1 | For THIS magic number; doesn't block manual trades |

### Signal Filters
| Input | Default | Notes |
|---|---|---|
| `Max_Signal_Age_Sec` | 1800 (30 min) | Skip signals older than this |
| `Take_Buy_Signals` | true | Disable to be sell-only |
| `Take_Sell_Signals` | true | Disable to be buy-only |
| `Required_Styles` | `swing,intraday,scalp` | CSV list. Set to `swing` only if you only want H4 setups |

### Trade Management
| Input | Default | Notes |
|---|---|---|
| `BE_Trigger_R` | 1.0 | Move SL to BE at this R multiple |
| `BE_Buffer_Points` | 2.0 | Tiny buffer past entry for spread |
| `Use_Partial_Close` | true | Take partial profits |
| `Partial_R` | 1.5 | R multiple to close partial |
| `Partial_Percent` | 50.0 | % of position to close |
| `Use_Trailing` | true | Trail SL after partial |
| `Trail_ATR_Mult` | 0.5 | Trail distance as N × H1 ATR |

### Identity
| Input | Default | Notes |
|---|---|---|
| `Magic_Number` | 4040405 | Unique ID for this EA's positions. Don't change after first deploy. |
| `Trade_Comment` | `xau-autotrader` | Visible in MT5 trade history |

## How the signal pipeline reaches the EA

```
Cron fires (07:00 UTC) — or you send /best from WhatsApp
   ↓
GitHub Actions runs run_auto.py
   ↓
generate_signal.py produces signal.json
   ↓
run_auto.py also writes data/signals/latest.json (tracked)
   ↓
Workflow commits + pushes to repo
   ↓
EA polls https://raw.githubusercontent.com/Bonquet/trading_setup/main/data/signals/latest.json
   ↓
Sees new signal_id, opens market order
```

End-to-end latency from cron to fill: ~1–2 minutes (GitHub Actions ~30s + commit propagation ~10s + EA poll wait ≤30s + execution).

## Safety guardrails the EA enforces

- **Magic number isolation** — only manages positions opened by this EA. Your manual trades are untouched.
- **Duplicate prevention** — tracks last_signal_id in `MQL5/Files/xau_autotrader_state.txt`. Same signal won't be taken twice even after MT5 restart.
- **Max open positions** — won't pile on. Default 1 = one EA position at a time.
- **Max trades per day** — default 5. After hitting limit, polling continues (state checks) but no new orders.
- **Stop-loss is set on every order** — never an "exposed" position. If your broker rejects SL/TP at order time, the trade is logged as failed.
- **Lot size capped** — Min_Lot and Max_Lot inputs are hard limits.

## What the EA does NOT do

- Open trades without a signal from the bot
- Trade outside XAUUSD (or your override symbol)
- Modify positions opened by other EAs or manual trades
- Move SL adversely (only improves)
- Send WhatsApp (the bot's existing Twilio pipeline handles that)

## Disable / re-enable

- Click **AutoTrading** toolbar button to red → EA stays attached but cannot trade
- Right-click chart → **Expert Advisors → Remove** → EA stops entirely
- Open positions stay open and you manage them manually

## Troubleshooting

| Symptom | Fix |
|---|---|
| `WebRequest error 4060` | Add `https://raw.githubusercontent.com` to allowed URLs |
| `AutoTrading disabled` | Click the AutoTrading button on the MT5 toolbar |
| `Symbol XAUUSD not found` | Set `Symbol_Override` to your broker's gold symbol (look in Market Watch) |
| `HTTP 404` | Bot hasn't fired any signal yet — `data/signals/latest.json` doesn't exist |
| `retcode=10006 (no money)` | Your balance is too low for the calculated lot. Reduce `Risk_Percent`. |
| `retcode=10018 (market closed)` | Weekend or rollover. EA will retry next poll. |
| EA frowny face | Either AutoTrading off, or DLL imports blocked (this EA doesn't use any — won't be the issue) |
| Positions stay at full size after +1.5R | Check `Use_Partial_Close` is true and broker allows partial closes |
| SL doesn't move to BE | Confirm BE_Trigger_R hit on H1 chart; check Experts tab for errors |

## Removing the EA cleanly

If you want to back out:
1. Right-click chart → Expert Advisors → Remove
2. Close any open positions manually in MT5
3. Delete `MQL5/Files/xau_autotrader_state.txt` to clear deduplication state

The bot's WhatsApp signals continue regardless — they're not coupled to the EA.

## Important reminders for prop firm compliance

- **GoatFunded confirmed allows EAs** per your message — but verify what they consider auto-trading vs trader-controlled.
- The bot still produces signals on its own schedule (cron). You can disable the EA at any time and the bot just becomes signal-only again.
- For the most conservative prop firm interpretation, run the EA with `Required_Styles=swing` only (H4 setups, low frequency) and set `Max_Trades_Per_Day=2` to look like a discretionary swing trader.
- Don't run multiple instances of this EA on multiple accounts with the same magic number — it'll get confused. Change the Magic_Number per chart if you do.

## Testing the EA (Strategy Tester + Demo)

`WebRequest()` is permanently blocked in the Strategy Tester — you can't backtest the live URL fetch path. But you CAN test everything else (entry, SL/TP placement, BE at +1R, partial close at +1.5R, trailing) using **Test Mode**.

### Test Mode setup

1. **Copy a test signal file into MT5's Files folder:**
   - File → Open Data Folder → navigate to `MQL5\Files\`
   - Copy `mt5/test_signals/test_signal_buy.json` (or `_sell.json`) from this repo into that folder

2. **Attach the EA** (either to a live chart OR in Strategy Tester):
   - In the input dialog, set `Test_Mode_File` = `test_signal_buy.json`
   - Other inputs as normal
   - Click OK

3. **Watch the EA pick up the test signal:**
   - In Experts tab, you should see `[OPEN] BUY XAUUSD @ ...`
   - The EA will use the signal's SL/TP but recalculate lots from current account balance + Risk_Percent
   - Manage the resulting position (BE / partial / trail) just like a real signal

4. **To simulate a "No Trade" condition:**
   - Use `test_signal_notrade.json` — EA reads it, sees `"decision": "No Trade"`, does nothing

5. **To re-trigger after the EA processes it:**
   - The EA tracks `signal_id` to prevent duplicates. Edit the file and change `"signal_id": "TEST_BUY_001"` to `"TEST_BUY_002"`. Save. EA picks it up on next poll.

### Strategy Tester workflow

1. Press **Ctrl+R** to open Strategy Tester
2. Expert: `XAU_AutoTrader`
3. Symbol: XAUUSD (or your broker's gold symbol)
4. Period: M15 or H1 (doesn't really matter — Test Mode isn't time-dependent)
5. Modeling: Every tick based on real ticks (most accurate)
6. Inputs tab → set `Test_Mode_File` = `test_signal_buy.json`
7. Start

The Test Mode reads the file once at the configured `signal_id`, opens a trade, and lets the tester run forward to see how the trade manager handles the position over time.

**Note**: Strategy Tester's historical data won't include the time when your test_signal was "published" (the timestamp in the JSON). The EA's `Max_Signal_Age_Sec` check might reject the signal as too old. Either:
- Set `Max_Signal_Age_Sec = 999999999` for testing
- Or update the JSON's `published_at_utc` to a date within the tester's range

### Demo account workflow (recommended over Strategy Tester)

Strategy Tester is fine for sanity-checking trade management. For full end-to-end validation including the WebRequest signal pipeline, use a **demo account**:

1. **File → Login to Trade Account → Open new demo account** (any broker offering XAU)
2. Attach the EA to the demo account's XAUUSD chart
3. Leave `Test_Mode_File` empty so it uses live signals from your bot
4. Trigger `/best` or `/scalp` from your WhatsApp — the bot writes a real signal to GitHub, the EA picks it up on the demo account
5. Watch real trades execute on demo money

This is closer to production behavior than the Strategy Tester.

## File layout in this repo

```
mt5/
├── README.md                  (this file)
└── ea/
    └── XAU_AutoTrader.mq5     (the EA — copy to MT5's Experts/ folder)

data/
├── cache/signal.json          (gitignored — bot's internal cache)
└── signals/
    ├── latest.json            (tracked — EA reads from raw.githubusercontent.com)
    └── history/               (tracked — every signal ever published)
```

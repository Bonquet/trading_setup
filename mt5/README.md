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

## Three EA files — purpose-built for different jobs

| File | Purpose | Signals come from | Where to run |
|---|---|---|---|
| **`XAU_AutoTrader.mq5`** | Live trading | Your bot via `WebRequest()` | Real or demo MT5 account |
| **`XAU_Strategy_Tester.mq5`** | **Backtest your REAL strategy** | Implements 50 EMA Williams rules **inline** | Strategy Tester (no internet needed) |
| **`XAU_AutoTrader_Tester.mq5`** | Validate trade-mgmt code | Synthetic alternating BUY/SELL every N hours | Strategy Tester (sanity check only) |

**For meaningful backtest results, use `XAU_Strategy_Tester.mq5`**. It mirrors the rules in `backtest/strategies/ema_williams.py` exactly:
- Long: Close > 50 EMA-High channel AND Williams %R crosses up through -20 AND Stoch %K > %D AND %K > 60 AND Close > EMA200
- Short: mirror
- Stop: recent 10-bar swing ± 0.5 × ATR(14)
- Target: 2R fixed
- Time exit: 50 bars

Python backtest results for this exact logic (22 years XAU, 2004–2026):

| TF | Trades | Win% | Expectancy | Profit Factor | Return | Max DD |
|---|---|---|---|---|---|---|
| **D1** ⭐ | 104 | **54.8%** | **+0.307R** | **1.82** | +30.9% | **-4.3%** |
| H4 | 651 | 44.9% | +0.096R | 1.16 | +68.2% | -14.8% |
| H1 | 2,495 | 43.7% | +0.048R | 1.09 | +168.1% | -26.7% |

Use D1 if you want the highest quality (Sharpe-like) trades. Use H4 if you want more activity. Use H1 for prop firm scaling speed (with accepted higher drawdown).

All EAs share **identical trade-management logic** — BE at +1R, partial 50% at +1.5R, trail SL by 0.5×ATR after partial.

The tester EA uses **Magic Number 4040406** to keep its positions separate from the live EA (Magic 4040405). You can have both attached to different charts without interference.

## Testing in the Strategy Tester

`WebRequest()` is permanently blocked in MT5's Strategy Tester — that's an MT5 design limitation. Use `XAU_AutoTrader_Tester.mq5` instead. It **generates its own synthetic signals internally** — no file, no folder hunt, no JSON setup. Just attach and run.

### Steps

1. **Compile the tester EA:**
   - In MetaEditor: open `XAU_AutoTrader_Tester.mq5` → F7

2. **Run the Strategy Tester:**
   - Ctrl+R → Strategy Tester opens
   - **Expert**: `XAU_AutoTrader_Tester`
   - **Symbol**: XAUUSD (or your broker's gold)
   - **Period**: M15 or H1
   - **Modeling**: Every tick based on real ticks
   - **Date range**: pick what you want (e.g. 2024-01-01 → 2024-12-31)
   - Defaults are fine — alternates BUY/SELL every 24 hours
   - **Start**

You should see in the journal:
```
[INIT] TESTER mode on XAUUSD | risk=1.0% | magic=4040406 | dir_mode=Alternating | trigger=24h
[INIT] Stop=300 points, TP=2.0R
[INIT] Trade mgmt: BE@+1.0R | Partial 50% @+1.5R | Trail 0.5xATR after partial
[OPEN] BUY XAUUSD @ XXXX.XX SL=XXXX.XX TP=XXXX.XX lots=0.0X risk=$XX.XX bal=$XXXX.XX
```

24h later:
```
[OPEN] SELL XAUUSD @ XXXX.XX SL=XXXX.XX TP=XXXX.XX ...
```

As price moves favorably:
```
[BE] ticket=XXXX SL->BE XXXX.XX at +1.00R
[PARTIAL] ticket=XXXX closed 0.0X at +1.51R
```

### Key tester inputs to play with

| Input | Default | What changes |
|---|---|---|
| `Direction_Mode` | `Alternating` | `BuyOnly`, `SellOnly`, `Random`, or `Alternating` |
| `Re_Trigger_Hours` | 24 | Lower = more trades per backtest, higher = fewer/cleaner |
| `Use_ATR_Stop` | **true** | Adaptive: stop = `ATR_Mult × H1 ATR`. Recommended for realistic XAU volatility (typically $10–25 stops). |
| `ATR_Mult` | 1.5 | Multiplier when `Use_ATR_Stop=true` |
| `Stop_Distance_Dollars` | 20.0 | Flat $ stop when `Use_ATR_Stop=false`. **In real dollars on XAU price**, not "points". 20.0 = $20 stop. |
| `TP_R_Multiple` | 2.0 | Target as N × stop distance |
| `BE_Trigger_R` | 1.0 | At what R-multiple the SL moves to BE |
| `Partial_R` | 1.5 | At what R-multiple to take 50% off |
| `Trail_ATR_Mult` | 0.5 | Trailing stop distance after partial |

### What the tester proves (and what it doesn't)

| ✅ Validates | ❌ Does NOT validate |
|---|---|
| BE-at-+1R correctness on real ticks | Whether the live bot picks good entries |
| Partial close at +1.5R | Real broker spread/slippage on your prop |
| Trailing SL after partial | WebRequest pipeline from GitHub → MT5 |
| Lot sizing math (against historical balance) | News spike handling |
| Direction handling (BUY and SELL) | Latency between bot signal and execution |
| Daily trade limit, max open positions | |

For end-to-end validation, use a **demo account** with the production `XAU_AutoTrader.mq5`. The tester EA is for proving the trade-management code is sane.

### Demo account workflow (closest to production)

Strategy Tester is fine for trade-management sanity checks. For full end-to-end validation including the live WebRequest pipeline, use a free demo account:

1. **File → Login to Trade Account → Open Demo** (any broker offering XAU)
2. Attach the **production** `XAU_AutoTrader` to the demo chart
3. Whitelist `https://raw.githubusercontent.com` (Tools → Options → Expert Advisors)
4. Send `/best` or `/scalp` from WhatsApp — bot writes a real signal to GitHub
5. Demo account picks up the signal and opens a trade with demo money

Same flow as live, just no real money at risk.

## File layout in this repo

```
mt5/
├── README.md                          (this file)
├── ea/
│   ├── XAU_AutoTrader.mq5             (PRODUCTION — copy to MQL5/Experts/, uses WebRequest)
│   └── XAU_AutoTrader_Tester.mq5      (TESTER — copy to MQL5/Experts/, reads local file)
└── test_signals/
    ├── test_signal_buy.json           (sample BUY signal — copy to MQL5/Files/)
    ├── test_signal_sell.json          (sample SELL signal — copy to MQL5/Files/)
    └── test_signal_notrade.json       (sample No-Trade — EA ignores it)

data/
├── cache/signal.json                  (gitignored — bot's internal cache)
└── signals/
    ├── latest.json                    (tracked — production EA reads from raw.githubusercontent.com)
    └── history/                       (tracked — every signal ever published)
```

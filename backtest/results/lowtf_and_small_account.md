# Lower Timeframes (15m/30m/1h) + Small-Account Reality

## Part A — Do 15m / 30m / 1h work on gold?

Tested all 5 strategies on 15m, 30m, 1h (full + out-of-sample, realistic costs).

### Verdict: lower = worse. 15m and 30m have NO viable edge.

| Timeframe | Result |
|---|---|
| **15m** | Every strategy **loses**. Best is -90% to -96%; donchian -338%; pullback wiped out. Costs + noise destroy the edge. |
| **30m** | Almost all negative. The one "positive" (breakout_retest +68%) has a -68% drawdown — unusable. |
| **1h** | Only TWO survive: **breakout_retest 1h** and **ema_williams 1h** — both positive in-sample AND out-of-sample, but with **big drawdowns (-27% to -42%)**. |

### The frequency vs. quality trade-off (this is your real decision)

| Strategy / TF | Trades/year | Profit Factor | Max Drawdown | Edge quality |
|---|---|---|---|---|
| ema_williams **1D** | ~5 | 1.82 | **-4.3%** | Best quality, slowest |
| ma_cross **4H** | ~9 | 1.67 | -6.1% | Best all-round |
| breakout_retest **4H** | ~51 (≈1/week) | 1.15 | -19.3% | Active, fragile to cost |
| ema_williams **1H** | ~113 (≈2/week) | 1.09 | -26.7% | Frequent, thin edge, deep DD |
| breakout_retest **1H** | ~176 (≈3/week) | 1.10 | -42.4% | Most frequent, worst DD |
| **15m / 30m** | very high | <1.0 | account-destroying | **No edge — do not trade** |

> You wanted more trades than 4H gives. The honest cost of that: dropping to 1H **quadruples-to-sixes the drawdown** (from ~5% to ~27-42%) for a much thinner edge. 15m/30m don't just trade more — they lose. There is no free lunch lower down on gold.

---

## Part B — Can a $20 account trade gold?

### Short answer: **No. Not on a standard account. It can't even open one trade.**

**The minimum lot (0.01) is a hard wall.** On XAUUSD, 0.01 lot = 1 oz, so $1 of price move = $1 P&L. Two problems on a tiny account:

### 1. Margin — you can't even open the position
At 1:100 leverage, opening 0.01 lot needs `price / 100` in margin:

| Gold price | Margin to open 0.01 lot |
|---|---|
| $2,000 | $20 |
| $3,000 | **$30** |
| $5,000 | **$50** |

> At today's ~$3,000+ gold, **a $20 account cannot open even the smallest trade** — it doesn't have the $30 margin.

### 2. Even if it could — the stop-loss IS the whole account
At the forced 0.01-lot minimum, your dollar risk = stop distance. A normal 1H stop is ~$25; a 4H stop ~$50. As a % of the account:

| Account | Risk per 1H trade ($25 stop) | Risk per 4H trade ($50 stop) |
|---|---|---|
| **$20** | **125%** (impossible) | **250%** |
| $50 | 50% | 100% |
| $100 | 25% | 50% |
| $500 | 5% | 10% |
| $1,000 | 2.5% | 5% |
| **$2,000** | **1.2%** | 2.5% |
| $5,000 | 0.5% | 1.0% |

> You asked exactly the right question: **yes, on a small account the stop-loss is basically the whole balance.** A single trade risks 25-250% of a $20-100 account. One normal losing streak = blown.

### Compounding simulation (start 2019, risk 1% of equity, margin + ruin enforced)

| Start | breakout_retest 1H → End | ema_williams 1H → End | Notes |
|---|---|---|---|
| **$20** | $12 (only 2 trades, then stuck) | $9 (1 trade) | Dead on arrival — margin blocks it |
| **$50** | $11 | **$4 (BUSTED)** | Forced over-risk; gambles, loses |
| **$100** | $1,903 *(but min equity hit $60, ~3.3% risk)* | $11 | Survives only by luck; very fragile |
| **$200** | $2,003 | $1,269 | Starts working, still ~2-5% risk |
| **$500** | $2,330 | $1,569 | Healthy, ~1.3-2.5% risk |
| **$1,000** | $2,800 | $2,064 | Safe ~1% risk, smooth compounding |
| **$5,000** | $11,336 | $7,723 | Clean compounding |

**Pattern:** small accounts take *fewer* trades (margin blocks them) AND are forced into *higher* risk — punished twice. The "$100 → $1,900" looks magic but it nearly busted (dipped to $60); $50 did bust. That's variance, not edge.

---

## Conclusions & recommended "grows-with-the-account" design

1. **$20 is not viable for gold on a standard account.** Hard stop.
2. **Two real ways to start small:**
   - **Cent / micro account** (your bot already ran on `XAUUSDm` — Exness cent style). On a cent account, balances and lots are 1/100th, so $20 behaves like ~$2,000 in lot terms → proper ~1% risk becomes possible. **This is the only realistic way a literal $20 trades gold.**
   - Or **start with ≥ $1,000** (ideally $2,000 for 1H, $5,000 for 4H) on a standard account.
3. **Minimum viable standard-account balances for ~1-2% risk:**
   - 1H strategies: **$1,000-$2,000**
   - 4H strategies: **$2,000-$5,000**
   - Daily strategies: **$5,000+** (bigger stops)
   - Below $500: not viable on gold.
4. **The compounding model is correct and already built in** — the engine sizes every trade as 1% of *current* equity, so lots grow as the account grows and shrink after losses. To make it growth-SAFE, add one rule:

   > **Min-lot safety gate:** if the smallest tradeable position (0.01 lot) would risk more than ~3-5% of current equity, **skip the trade.** This stops a tiny account from being forced into 25-250% risk. It means the bot simply waits/grows on a cent account until it can size properly — exactly the "grow with the account" behavior you want.

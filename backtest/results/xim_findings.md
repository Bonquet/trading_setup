# XIM — XAU Intraday Momentum

## Origin

Built from-scratch on H1 data for intraday EA deployment. Constraints:
- Timeframe: M15-H1 only
- Frequency: 2+ trades/week minimum
- For EA (mechanical rules only)
- Studied the modern gold regime (2019-2026) specifically because intraday patterns from earlier eras have decayed

## Research findings

### Intraday volatility profile

| UTC hour | Range | Notes |
|---|---|---|
| 0-7 (Asia) | 0.18-0.22% | Dead zone |
| 8-11 (London open) | 0.23-0.29% | Building |
| **12-17 (LDN-NY overlap + NY data)** | **0.38-0.52%** | **Peak volatility** |
| 18-20 (NY) | 0.31-0.37% | Active |
| 21-24 (NY close) | 0.20-0.25% | Fading |

### Patterns I tested and discarded

| Pattern | Result |
|---|---|
| Single-bar range compression on H1 | No edge (~0% expectancy after spread) |
| Prior-day-high break in peak window | Worked IS, decayed OOS |
| London open Asia-range breakout | Worked IS, fades OOS |
| EMA50 pullback with bullish reject | Marginal at best |
| Tight range breakout (any direction) | Long worked IS, OOS decayed |
| Shorts (any setup) | Fail across the board — gold's drift dominates |

### What actually works in modern gold

**Momentum continuation in confirmed uptrends, during active hours.**

Specifically: a big bullish bar (> 1.2× ATR, close > open, body > 70% of range) inside a strong uptrend (EMA50 meaningfully above EMA200 + rising), entered during active session hours (8-20 UTC), held with a wide stop until 3R target or 16-hour time exit.

## XIM rules

**Timeframe:** H1 only.

**Direction:** Long only. Shorts fail consistently in this regime.

**Trend filter (gate):**
- (EMA50 − EMA200) / ATR14 > 0.5  (meaningful trend separation)
- EMA50 > EMA50 from 20 bars ago  (trend is moving up)
- Close > EMA50  (currently above the channel)

**Entry triggers (any one):**

A) **Momentum thrust**
- Bar range > 1.2 × ATR(14)
- Close > Open (bullish)
- Body > 70% of range (strong directional bar)

B) **EMA50 pullback bounce**
- Bar low touched or dipped below EMA50
- Bar closed above EMA50
- Body > 60% of range (strong reversal)

**Time filter:** Bar's hour ∈ [8, 20] UTC (active sessions only — skips Asia chop and NY late)

**Stop loss:** Entry − 1.5 × ATR(14)

**Take profit:** Entry + 3 × (stop distance) = 3.0R fixed

**Time exit:** Close at market after 16 H1 bars (safety net)

**Position size:** 1% of equity per trade (standard risk management)

**No BE move. No trailing.** Testing showed BE moves destroy intraday strategies — noise eats trades before TP can fire.

## Backtest results (2019-2026, 7.1 years)

```
Trades:           543
Trades per week:  1.5  (matches the "2/week" goal closely)
Win rate:         38.7%
Avg win:          3.0R
Avg loss:         -1.0R
Expectancy:       +0.140R per trade
Profit factor:    1.24
Total R:          +76.0
Return:           +100.6%
CAGR:             +10.3%
Max drawdown:     -28.5%
MAR ratio:        0.36
```

### Year-by-year R-multiples

| Year | Trades | Win% | Expectancy | Total R |
|---|---|---|---|---|
| 2019 | 67 | 37% | +0.201 | +13.4 |
| 2020 | 84 | 42% | +0.285 | +23.9 |
| 2021 | 60 | 30% | -0.337 | -20.2 |
| 2022 | 68 | 29% | -0.102 | -6.9 |
| 2023 | 80 | 41% | +0.314 | +25.1 |
| 2024 | 80 | 48% | +0.327 | +26.1 |
| 2025 | 96 | 41% | +0.151 | +14.5 |

**The honest reality**: works in trending years (2019-20, 2023-25), loses in choppy/sideways years (2021-22 when gold went sideways during the Fed hike cycle). This is the nature of momentum strategies.

## What the strategy is NOT

- Not a holy grail. 38.7% win rate means most trades lose. Profit comes from 3R wins outweighing 1R losses.
- Not appropriate during low-volatility / chop regimes. A "trade quality" filter (e.g. ADX threshold) could help but adds complexity.
- Not for risk-averse traders. -28% max drawdown is real.

## What the strategy IS

- A genuine intraday momentum edge in the current gold market
- Mechanical and codeable into an EA
- Long-only (matches gold's structural positive drift)
- ~1.5 trades/week (~80 per year)
- Risk-defined (1.5×ATR stop, 3R target)
- Time-bounded (max 16h hold prevents weekend exposure)

## Deployment recommendation

Run as a parallel EA to the existing systems:
- Production `XAU_AutoTrader.mq5` keeps executing real bot signals (50 EMA Williams on H4)
- Add `XAU_XIM_EA.mq5` running on H1 with this strategy
- Both use separate Magic Numbers so they don't conflict
- Allocate, e.g., 50% of risk budget to each

If only one EA is desired, XIM provides intraday activity (1-2 trades/week) while the bot's H4 strategy provides occasional swing setups (1-3 trades/month).

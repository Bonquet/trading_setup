# SMC (Smart Money Concepts) — Researched, Built, Backtested

## What I implemented (faithful to the published methodology)

Researched the canonical SMC/ICT rules and the gold-specific multi-timeframe approach,
then implemented them mechanically:

- **HTF bias** from higher-timeframe market structure (4H for 15m/30m/1h entries; Daily for 4H entries) — HH/HL = bullish, LH/LL = bearish. Trade only with the HTF trend.
- **Liquidity sweep** — price grabs the latest swing low (longs) / high (shorts) then closes back inside.
- **CHoCH / BOS** — structure shifts back with trend (close breaks the reference swing).
- **Entry** on that confirmation; **stop** beyond the liquidity-grab extreme; **target 1:2 RR** (SMC minimum).
- Built a real market-structure engine (`indicators.market_structure`) that detects BOS/CHoCH with no look-ahead, and a no-look-ahead HTF-bias aligner.

Timeframes tested: **15m, 30m, 1h** (4H bias) and **4h** (Daily bias). Same engine, costs, and out-of-sample split as every other strategy.

> Sources: strike.money SMC guide, the5ers, ACY gold-SMC guides, TradingView (VasilyTrader), Daily Price Action — see chat for links.

## Results — full period

| TF | Trades | Win% | PF (realistic) | Expectancy R | Return (realistic) | Max DD | MAR |
|---|---|---|---|---|---|---|---|
| 15m | 5,699 | 38.0 | 0.90 | -0.060 | **-90.4%** | -97.9% | -0.10 |
| 30m | 3,003 | 38.8 | 0.98 | -0.004 | -24.2% | -55.4% | -0.02 |
| 1h | 1,527 | 36.4 | 0.95 | -0.041 | -41.3% | -64.7% | -0.04 |
| **4h** | 341 | 41.3 | **1.18** | **0.115** | **+38.2%** | -10.3% | 0.15 |

## The key finding: SMC on gold is a COST TRAP on its own native timeframes

Look at the cost sensitivity — this is the whole story:

| TF | Return @ $0 cost | Return @ realistic cost | What happened |
|---|---|---|---|
| **15m** | **+834%** | **-90%** | Edge exists gross — **spread eats all of it and then some** |
| **30m** | +522% | -24% | Same: great gross, dead net |
| 1h | +8% | -41% | Marginal gross, negative net |
| 4h | +49% | +38% | **Survives costs** (few trades) |

**SMC genuinely has a gross edge** (huge zero-cost returns prove the liquidity/structure signal is real). But on the **15m/5m timeframes its own practitioners recommend**, the trade frequency (3,000-5,700 trades) means **transaction costs completely destroy it on gold.** +834% gross becomes -90% net.

> This is the *exact same disease* that kills your scalper bot. SMC doesn't escape it — on low timeframes, gold's spread is the boss. "Smart money" entries don't beat the spread when you take thousands of them.

## Out-of-sample check (realistic costs)

| TF | Expectancy IS → OOS | Verdict |
|---|---|---|
| 4h | 0.16 → 0.02 | positive but **fading** out-of-sample |
| 30m | -0.03 → 0.04 | inconsistent (negative IS) |
| 1h | -0.02 → -0.09 | negative both — reject |
| 15m | -0.07 → -0.04 | negative both — reject |

Only 4H SMC is positive in both halves, and even there the edge is weakening.

## Verdict: SMC is NOT the best strategy for gold

Ranked against everything tested (full period, realistic costs, by MAR):

| Rank | Strategy | TF | PF | Max DD | MAR | Survives costs + OOS? |
|---|---|---|---|---|---|---|
| 1 | ma_cross (50/200 trend) | 4H | 1.67 | -6.1% | **0.36** | ✅ yes |
| 2 | breakout_retest | 1D | 1.62 | -9.1% | 0.31 | ✅ yes |
| 3 | ema_williams (your playbook) | 1D | 1.82 | -4.3% | 0.29 | ✅ yes |
| … | **smc** | **4H** | **1.18** | **-10.3%** | **0.15** | 🟡 cost-ok but fading OOS |
| ✗ | smc | 15m/30m/1h | <1.0 | huge | negative | ❌ cost trap |

**Bottom line:** SMC's best showing (4H) lands mid-pack — below the simple 50/200 trend and your own 50 EMA Williams on Daily, and it's decaying out-of-sample. On the low timeframes SMC is famous for, it's a **net loser on gold purely because of spread**, despite a real gross edge.

The lesson is now consistent across **everything** tested: **on gold, higher timeframe + fewer trades wins; low-timeframe systems (your scalper, low-TF SMC) lose to costs no matter how clever the entry logic.**

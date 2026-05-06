# XAUUSD Trade Journal

Format: one trade per block, newest at top. Claude appends after user confirms a fill or exit.

---

## Template (copy this for each new idea)

```
### YYYY-MM-DD HH:MM UTC — [BUY/SELL] @ <entry>
- Session: London / NY
- Bias: D1 <bull/bear>, H4 <bull/bear>
- Setup: <50 EMA reclaim / pullback to 50 fib / pivot reversal / etc.>
- Entry: <price>
- SL: <price> (<pips>)
- TP1: <price> (1.0R, target pivot X)
- TP2: <price> (2.0R+, target pivot Y)
- Size: <lots> @ 1% risk of $<account>
- Confluence ticked: [x] 50 EMA cross [x] Williams %R [x] Stoch [x] Fib/PSAR [x] Pivot room [x] Bias align
- Outcome: <pending / filled / missed / SL / TP1 / TP2 / BE>
- R result: <+2.0R / -1.0R / +0.5R / 0>
- Notes: <what worked, what didn't, rule adherence>
```

---

## Trades

<!-- Append new entries above this line -->

### 2026-04-28 07:17 UTC — SELL @ 4632.94
- Session: manual
- Strategy: 50 EMA Williams
- SL: 4707.24 | TP1: 4484.33 | TP2: 4484.33
- RR: 2.0R | Size: 0.01 lots | Risk: 1% of $5000.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -90.1, 'stoch_k': 16.9, 'stoch_d': 21.2}
- Outcome: pending

### 2026-04-28 08:10 UTC — SELL @ 4621.64
- Session: manual
- Strategy: 50 EMA Williams (intraday)
- SL: 4645.23 | TP1: 4574.45 | TP2: 4574.45
- RR: 2.0R | Size: 0.01 lots | Risk: 1% of $5000.0
- Confluence: {'H4_position': 'below_channel', 'H1_position': 'below_channel', 'williams_r14': -96.4, 'stoch_k': 9.0, 'stoch_d': 9.3}
- Outcome: pending

### 2026-04-28 12:32 UTC — SELL @ 4577.03
- Session: manual
- Strategy: 50 EMA Williams (swing)
- SL: 4615.11 | TP1: 4500.87 | TP2: 4481.83
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $5000.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -90.0, 'stoch_k': 7.6, 'stoch_d': 15.3}
- Outcome: pending

### 2026-04-28 12:33 UTC — SELL @ 4581.94
- Session: manual
- Strategy: 50 EMA Williams (swing)
- SL: 4620.02 | TP1: 4505.78 | TP2: 4486.74
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $5000.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -87.8, 'stoch_k': 8.4, 'stoch_d': 15.6}
- Outcome: pending

### 2026-04-29 07:03 UTC — SELL @ 4586.03
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4613.12 | TP1: 4531.85 | TP2: 4518.3
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4923.84
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -83.3, 'stoch_k': 23.8, 'stoch_d': 24.5}
- Outcome: pending

### 2026-04-29 09:06 UTC — SELL @ 4575.24
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4613.11 | TP1: 4499.5 | TP2: 4472.38
- RR: 2.72R | Size: 0.01 lots | Risk: 1% of $4923.84
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -89.2, 'stoch_k': 16.9, 'stoch_d': 21.7}
- Outcome: pending

### 2026-04-29 15:08 UTC — SELL @ 4542.69
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4585.8 | TP1: 4456.46 | TP2: 4434.9
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $5094.43
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -83.1, 'stoch_k': 10.0, 'stoch_d': 15.3}
- Outcome: pending

### 2026-05-06 09:59 UTC — BUY @ 4701.51
- Session: manual-scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4692.27 | TP1: 4710.74 | TP2: 4715.35
- RR: 1.5R | Size: 0.05 lots | Risk: 1% of $4820.49
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -7.8, 'stoch_k': 90.1, 'stoch_d': 89.3}
- Outcome: pending

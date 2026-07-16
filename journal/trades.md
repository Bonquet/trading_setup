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

### 2026-05-12 15:38 UTC — SELL @ 4661.37
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4704.8 | TP1: 4574.52 | TP2: 4552.81
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -85.0, 'stoch_k': 34.0, 'stoch_d': 46.8}
- Outcome: pending

### 2026-05-15 09:40 UTC — SELL @ 4546.36
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4593.94 | TP1: 4451.22 | TP2: 4427.43
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -97.8, 'stoch_k': 1.3, 'stoch_d': 4.4}
- Outcome: pending

### 2026-05-20 06:36 UTC — SELL @ 4464.12
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4509.44 | TP1: 4373.5 | TP2: 4350.84
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -90.8, 'stoch_k': 13.3, 'stoch_d': 16.9}
- Outcome: pending

### 2026-05-26 16:39 UTC — SELL @ 4509.78
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4541.88 | TP1: 4445.59 | TP2: 4429.54
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -88.8, 'stoch_k': 20.3, 'stoch_d': 26.7}
- Outcome: pending

### 2026-05-27 10:51 UTC — SELL @ 4447.11
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4485.6 | TP1: 4370.13 | TP2: 4350.88
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -99.5, 'stoch_k': 15.8, 'stoch_d': 24.0}
- Outcome: pending

### 2026-05-28 10:47 UTC — SELL @ 4387.72
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4434.18 | TP1: 4294.8 | TP2: 4271.57
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4945.22
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -88.1, 'stoch_k': 8.6, 'stoch_d': 14.9}
- Outcome: pending

### 2026-06-05 15:49 UTC — SELL @ 4339.27
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4394.96 | TP1: 4227.88 | TP2: 4200.03
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4531.24
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -97.4, 'stoch_k': 15.9, 'stoch_d': 24.5}
- Outcome: pending

### 2026-06-10 10:50 UTC — SELL @ 4176.3
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4229.77 | TP1: 4069.34 | TP2: 4042.6
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $4531.24
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -92.5, 'stoch_k': 4.3, 'stoch_d': 6.6}
- Outcome: pending

### 2026-06-18 11:05 UTC — SELL @ 4251.15
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4306.86 | TP1: 4139.75 | TP2: 4111.9
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $200.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -81.0, 'stoch_k': 35.6, 'stoch_d': 43.0}
- Outcome: pending

### 2026-06-18 16:25 UTC — SELL @ 4223.34
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4281.84 | TP1: 4106.32 | TP2: 4077.06
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $200.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -98.3, 'stoch_k': 15.8, 'stoch_d': 32.8}
- Outcome: pending

### 2026-06-23 06:36 UTC — SELL @ 4115.7
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4154.24 | TP1: 4038.64 | TP2: 4019.37
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $200.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -92.1, 'stoch_k': 27.3, 'stoch_d': 48.2}
- Outcome: pending

### 2026-06-24 08:16 UTC — SELL @ 4076.43
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4106.99 | TP1: 4015.3 | TP2: 4000.02
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $200.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -85.5, 'stoch_k': 11.1, 'stoch_d': 13.7}
- Outcome: pending

### 2026-06-24 10:15 UTC — SELL @ 4060.51
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4105.2 | TP1: 3971.14 | TP2: 3948.8
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $200.0
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -93.0, 'stoch_k': 10.8, 'stoch_d': 11.2}
- Outcome: pending

### 2026-06-25 11:32 UTC — SELL @ 3979.28
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4016.02 | TP1: 3905.78 | TP2: 3872.55
- RR: 2.9R | Size: 0.01 lots | Risk: 1% of $769.98
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -91.1, 'stoch_k': 11.8, 'stoch_d': 13.1}
- Outcome: pending

### 2026-06-29 11:53 UTC — SELL @ 4036.82
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4066.25 | TP1: 3977.95 | TP2: 3963.23
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $733.24
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -82.9, 'stoch_k': 10.2, 'stoch_d': 25.0}
- Outcome: pending

### 2026-07-01 06:29 UTC — SELL @ 3968.12
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4010.03 | TP1: 3884.3 | TP2: 3863.35
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $806.83
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -85.0, 'stoch_k': 22.9, 'stoch_d': 32.4}
- Outcome: pending

### 2026-07-01 08:10 UTC — SELL @ 3972.2
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4014.54 | TP1: 3887.54 | TP2: 3866.38
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $806.83
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -82.6, 'stoch_k': 23.6, 'stoch_d': 32.7}
- Outcome: pending

### 2026-07-08 15:15 UTC — SELL @ 4036.33
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4084.83 | TP1: 3939.35 | TP2: 3915.1
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $722.58
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -99.6, 'stoch_k': 8.2, 'stoch_d': 14.0}
- Outcome: pending

### 2026-07-08 15:33 UTC — SELL @ 4022.89
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4034.22 | TP1: 4011.57 | TP2: 4005.9
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $722.58
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -98.9, 'stoch_k': 2.4, 'stoch_d': 4.7}
- Outcome: pending

### 2026-07-15 12:42 UTC — BUY @ 4060.6
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4052.98 | TP1: 4068.22 | TP2: 4072.03
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $662.75
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -0.3, 'stoch_k': 81.9, 'stoch_d': 80.3}
- Outcome: pending

### 2026-07-16 14:56 UTC — SELL @ 3995.09
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4041.25 | TP1: 3902.79 | TP2: 3879.72
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $674.18
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -84.4, 'stoch_k': 18.5, 'stoch_d': 30.5}
- Outcome: pending

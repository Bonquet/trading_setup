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

### 2026-07-16 17:46 UTC — SELL @ 3981.22
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 3991.29 | TP1: 3971.14 | TP2: 3966.1
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $674.18
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -99.5, 'stoch_k': 6.1, 'stoch_d': 14.2}
- Outcome: pending

### 2026-07-23 12:58 UTC — SELL @ 4065.5
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4073.34 | TP1: 4057.66 | TP2: 4053.75
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $674.18
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -92.2, 'stoch_k': 10.9, 'stoch_d': 21.1}
- Outcome: pending

### 2026-07-28 15:16 UTC — SELL @ 4034.47
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4055.1 | TP1: 4013.84 | TP2: 3993.19 | TP3: 3964.38
- RR: 3.4R | Size: 0.01 lots | Risk: 1% of $816.42
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -80.8, 'stoch_k': 22.0, 'stoch_d': 27.4}
- Outcome: pending

### 2026-07-29 15:06 UTC — SELL @ 4008.3
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4041.88 | TP1: 3974.72 | TP2: 3941.15 | TP3: 3924.36
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $816.42
- Confluence: {'D1_position': 'below_channel', 'H4_position': 'below_channel', 'williams_r14': -90.0, 'stoch_k': 16.6, 'stoch_d': 17.4}
- Outcome: pending

### 2026-07-29T17:55Z - CLOSED SELL #20260729T150619Z_e14e32
- Entry: 4008.3 | Exit: 4041.88 (SL hit)
- Targets: TP1 3974.72 | TP2 3941.15 | TP3 3924.36
- Outcome: loss | -1.0R | P&L: $-33.58

### 2026-07-30 09:29 UTC — BUY @ 4069.44
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4059.96 | TP1: 4078.92 | TP2: 4083.66
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $782.84
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -2.1, 'stoch_k': 84.9, 'stoch_d': 83.1}
- Outcome: pending

### 2026-07-30T14:35Z - CLOSED BUY #20260730T092909Z_cde64d
- Entry: 4069.44 | Exit: 4083.66 (TP2 hit)
- Targets: TP1 4078.92 | TP2 4083.66
- Outcome: win | 1.5R | P&L: $14.22

### 2026-08-03 13:30 UTC — SELL @ 4034.72
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4041.89 | TP1: 4027.55 | TP2: 4023.97
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $797.06
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -97.2, 'stoch_k': 10.7, 'stoch_d': 14.3}
- Outcome: pending

### 2026-08-03T14:55Z - CLOSED SELL #20260803T133027Z_1a9ac6
- Entry: 4034.72 | Exit: 4023.97 (TP2 hit)
- Targets: TP1 4027.55 | TP2 4023.97
- Outcome: win | 1.5R | P&L: $10.75

### 2026-08-05 15:10 UTC — BUY @ 4257.07
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4209.03 | TP1: 4305.11 | TP2: 4353.15 | TP3: 4377.17
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $807.81
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -2.2, 'stoch_k': 90.2, 'stoch_d': 88.0}
- Outcome: pending

### 2026-08-07 08:08 UTC — BUY @ 4295.4
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4243.46 | TP1: 4347.35 | TP2: 4399.30 | TP3: 4425.27
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $807.81
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -4.2, 'stoch_k': 83.2, 'stoch_d': 77.4}
- Outcome: pending

### 2026-08-10T19:11Z - CLOSED BUY #20260805T151027Z_cd5981
- Entry: 4257.07 | Exit: 4377.17 (TP3 hit)
- Targets: TP1 4305.11 | TP2 4353.15 | TP3 4377.17
- Outcome: win | 2.5R | P&L: $120.10

### 2026-08-10 19:41 UTC — BUY @ 4389.69
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4382.32 | TP1: 4397.06 | TP2: 4400.75
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $927.91
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -10.0, 'stoch_k': 95.5, 'stoch_d': 94.2}
- Outcome: pending

### 2026-08-10T23:20Z - CLOSED BUY #20260810T194143Z_d95614
- Entry: 4389.69 | Exit: 4400.75 (TP2 hit)
- Targets: TP1 4397.06 | TP2 4400.75
- Outcome: win | 1.5R | P&L: $11.06

### 2026-08-11T02:52Z - CLOSED BUY #20260807T080820Z_3572ff
- Entry: 4295.4 | Exit: 4425.27 (TP3 hit)
- Targets: TP1 4347.35 | TP2 4399.30 | TP3 4425.27
- Outcome: win | 2.5R | P&L: $129.87

### 2026-08-11 11:05 UTC — BUY @ 4391.98
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4384.67 | TP1: 4399.28 | TP2: 4402.94
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1068.84
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -1.3, 'stoch_k': 91.7, 'stoch_d': 91.3}
- Outcome: pending

### 2026-08-11T11:55Z - CLOSED BUY #20260811T110523Z_a8d3ca
- Entry: 4391.98 | Exit: 4384.67 (SL hit)
- Targets: TP1 4399.28 | TP2 4402.94
- Outcome: loss | -1.0R | P&L: $-7.31

### 2026-08-12 14:17 UTC — BUY @ 4434.11
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4389.79 | TP1: 4478.44 | TP2: 4522.77 | TP3: 4544.94
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $1061.53
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -7.7, 'stoch_k': 87.6, 'stoch_d': 78.4}
- Outcome: pending

### 2026-08-13T06:44Z - CLOSED BUY #20260812T141753Z_00f14e
- Entry: 4434.11 | Exit: 4389.79 (SL hit)
- Targets: TP1 4478.44 | TP2 4522.77 | TP3 4544.94
- Outcome: loss | -1.0R | P&L: $-44.32

### 2026-08-13 16:11 UTC — SELL @ 4360.06
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4369.52 | TP1: 4350.59 | TP2: 4345.85
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1017.21
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -93.9, 'stoch_k': 15.8, 'stoch_d': 19.7}
- Outcome: pending

### 2026-08-13T17:29Z - CLOSED SELL #20260813T161125Z_2a36d3
- Entry: 4360.06 | Exit: 4369.52 (SL hit)
- Targets: TP1 4350.59 | TP2 4345.85
- Outcome: loss | -1.0R | P&L: $-9.46

### 2026-08-14 12:10 UTC — BUY @ 4372.11
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4366.26 | TP1: 4377.96 | TP2: 4380.88
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1007.75
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -5.5, 'stoch_k': 96.9, 'stoch_d': 93.0}
- Outcome: pending

### 2026-08-14T13:35Z - CLOSED BUY #20260814T121008Z_40e80b
- Entry: 4372.11 | Exit: 4380.88 (TP2 hit)
- Targets: TP1 4377.96 | TP2 4380.88
- Outcome: win | 1.5R | P&L: $8.77

### 2026-08-17 07:44 UTC — BUY @ 4409.7
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4384.98 | TP1: 4434.43 | TP2: 4459.16 | TP3: 4471.52
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $1016.52
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -9.6, 'stoch_k': 80.0, 'stoch_d': 65.4}
- Outcome: pending

### 2026-08-17 07:51 UTC — BUY @ 4407.95
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4401.24 | TP1: 4414.67 | TP2: 4418.03
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1016.52
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -10.0, 'stoch_k': 94.0, 'stoch_d': 87.6}
- Outcome: pending

### 2026-08-17T08:06Z - CLOSED BUY #20260817T075106Z_6ef27c
- Entry: 4407.95 | Exit: 4401.24 (SL hit)
- Targets: TP1 4414.67 | TP2 4418.03
- Outcome: loss | -1.0R | P&L: $-6.71

### 2026-08-17T13:05Z - CLOSED BUY #20260817T074431Z_b3eb4e
- Entry: 4409.7 | Exit: 4384.98 (SL hit)
- Targets: TP1 4434.43 | TP2 4459.16 | TP3 4471.52
- Outcome: loss | -1.0R | P&L: $-24.72

### 2026-08-17 15:58 UTC — BUY @ 4426.94
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4418.74 | TP1: 4435.13 | TP2: 4439.22
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $985.09
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -0.0, 'stoch_k': 94.5, 'stoch_d': 90.5}
- Outcome: pending

### 2026-08-17T17:26Z - CLOSED BUY #20260817T155833Z_d8ad3a
- Entry: 4426.94 | Exit: 4418.74 (SL hit)
- Targets: TP1 4435.13 | TP2 4439.22
- Outcome: loss | -1.0R | P&L: $-8.20

### 2026-08-18 19:26 UTC — SELL @ 4354.14
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4360.85 | TP1: 4347.43 | TP2: 4344.07
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $976.89
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -93.2, 'stoch_k': 11.1, 'stoch_d': 14.1}
- Outcome: pending

### 2026-08-18T19:56Z - CLOSED SELL #20260818T192616Z_ec0cb3
- Entry: 4354.14 | Exit: 4344.07 (TP2 hit)
- Targets: TP1 4347.43 | TP2 4344.07
- Outcome: win | 1.5R | P&L: $10.07

### 2026-08-18 20:20 UTC — SELL @ 4340.12
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4346.93 | TP1: 4333.32 | TP2: 4329.92
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $986.96
- Confluence: {'H1_position': 'below_channel', 'M15_position': 'below_channel', 'williams_r14': -93.5, 'stoch_k': 8.7, 'stoch_d': 10.4}
- Outcome: pending

### 2026-08-18T23:42Z - CLOSED SELL #20260818T202042Z_7a01d7
- Entry: 4340.12 | Exit: 4329.92 (TP2 hit)
- Targets: TP1 4333.32 | TP2 4329.92
- Outcome: win | 1.5R | P&L: $10.20

### 2026-08-19 13:39 UTC — BUY @ 4456.88
- Session: ny
- Strategy: 50 EMA Williams (swing)
- SL: 4410.99 | TP1: 4502.76 | TP2: 4548.65 | TP3: 4571.59
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $997.16
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -14.0, 'stoch_k': 69.6, 'stoch_d': 45.5}
- Outcome: pending

### 2026-08-19 16:28 UTC — BUY @ 4492.24
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4480.44 | TP1: 4504.04 | TP2: 4509.94
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $997.16
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -5.8, 'stoch_k': 96.7, 'stoch_d': 95.9}
- Outcome: pending

### 2026-08-19T18:57Z - CLOSED BUY #20260819T162824Z_7e7e3f
- Entry: 4492.24 | Exit: 4480.44 (SL hit)
- Targets: TP1 4504.04 | TP2 4509.94
- Outcome: loss | -1.0R | P&L: $-11.80

### 2026-08-19 20:36 UTC — BUY @ 4520.62
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4511.02 | TP1: 4530.23 | TP2: 4535.03
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $985.36
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -0.3, 'stoch_k': 93.0, 'stoch_d': 91.0}
- Outcome: pending

### 2026-08-20T01:41Z - CLOSED BUY #20260819T203634Z_bdf4bb
- Entry: 4520.62 | Exit: 4511.02 (SL hit)
- Targets: TP1 4530.23 | TP2 4535.03
- Outcome: loss | -1.0R | P&L: $-9.60

### 2026-08-20 08:18 UTC — BUY @ 4497.88
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4491.78 | TP1: 4503.98 | TP2: 4507.03
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $975.76
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -3.3, 'stoch_k': 81.2, 'stoch_d': 68.3}
- Outcome: pending

### 2026-08-20T08:59Z - CLOSED BUY #20260820T081809Z_9370dd
- Entry: 4497.88 | Exit: 4491.78 (SL hit)
- Targets: TP1 4503.98 | TP2 4507.03
- Outcome: loss | -1.0R | P&L: $-6.10

### 2026-08-20 15:17 UTC — BUY @ 4536.88
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4525.94 | TP1: 4547.81 | TP2: 4553.28
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $969.66
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -6.0, 'stoch_k': 97.5, 'stoch_d': 96.5}
- Outcome: pending

### 2026-08-20T15:51Z - CLOSED BUY #20260820T151738Z_a43ec0
- Entry: 4536.88 | Exit: 4525.94 (SL hit)
- Targets: TP1 4547.81 | TP2 4553.28
- Outcome: loss | -1.0R | P&L: $-10.94

### 2026-08-21 07:36 UTC — BUY @ 4561.5
- Session: london
- Strategy: 50 EMA Williams (swing)
- SL: 4509.61 | TP1: 4613.39 | TP2: 4665.29 | TP3: 4691.23
- RR: 2.5R | Size: 0.01 lots | Risk: 1% of $958.72
- Confluence: {'D1_position': 'above_channel', 'H4_position': 'above_channel', 'williams_r14': -2.2, 'stoch_k': 93.1, 'stoch_d': 89.7}
- Outcome: pending

### 2026-08-21T08:52Z - CLOSED BUY #20260819T133945Z_bfb14f
- Entry: 4456.88 | Exit: 4571.59 (TP3 hit)
- Targets: TP1 4502.76 | TP2 4548.65 | TP3 4571.59
- Outcome: win | 2.5R | P&L: $114.71

### 2026-08-21 15:50 UTC — BUY @ 4608.25
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4597.24 | TP1: 4619.26 | TP2: 4624.77
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1073.43
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -3.0, 'stoch_k': 97.2, 'stoch_d': 89.5}
- Outcome: pending

### 2026-08-21T16:51Z - CLOSED BUY #20260821T155014Z_e589b1
- Entry: 4608.25 | Exit: 4624.77 (TP2 hit)
- Targets: TP1 4619.26 | TP2 4624.77
- Outcome: win | 1.5R | P&L: $16.52

### 2026-08-21 17:06 UTC — BUY @ 4626.93
- Session: scalp
- Strategy: 50 EMA Williams (scalp)
- SL: 4616.77 | TP1: 4637.08 | TP2: 4642.16
- RR: 1.5R | Size: 0.01 lots | Risk: 1% of $1089.95
- Confluence: {'H1_position': 'above_channel', 'M15_position': 'above_channel', 'williams_r14': -0.5, 'stoch_k': 99.6, 'stoch_d': 96.6}
- Outcome: pending

### 2026-08-21T17:46Z - CLOSED BUY #20260821T170600Z_7676ec
- Entry: 4626.93 | Exit: 4616.77 (SL hit)
- Targets: TP1 4637.08 | TP2 4642.16
- Outcome: loss | -1.0R | P&L: $-10.16

### 2026-08-25T00:35Z - CLOSED BUY #20260821T073559Z_8a07aa
- Entry: 4561.5 | Exit: 4691.23 (TP3 hit)
- Targets: TP1 4613.39 | TP2 4665.29 | TP3 4691.23
- Outcome: win | 2.5R | P&L: $129.73

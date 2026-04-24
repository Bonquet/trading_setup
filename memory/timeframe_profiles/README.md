# timeframe_profiles/

One file per timeframe. Track: signal quality, avg win rate, avg RR, whipsaw frequency, trend reliability, suitability for Pullback, suitability for 50 EMA Williams.

Filename: `<tf>.md` — e.g. `H4.md`, `H1.md`, `M15.md`, `D1.md`.

Seeds:
- **D1:** best for bias, poor for entries (too slow to react).
- **H4:** primary setup TF for both strategies. Cleanest signals, lowest whipsaw.
- **H1:** entry timing; acceptable signal quality if HTF aligned.
- **M15:** trigger only — never standalone. Whipsaw-prone.

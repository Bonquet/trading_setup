"""
Strategy package. Each module exposes:

    generate(df: pd.DataFrame, tf: str) -> dict with keys:
        signals : DataFrame[dir, stop, target, exit]  (index == df.index)
        atr_series   : optional pd.Series for trailing
        atr_trail_mult : optional float
        max_bars : optional int

REGISTRY maps name -> (module.generate, [timeframes]).
"""
from . import ema_williams, pullback, donchian, ma_cross, breakout_retest, slow_trend

REGISTRY = {
    "ema_williams":     (ema_williams.generate,    ["1h", "4h", "1d"]),
    "pullback":         (pullback.generate,         ["1h", "4h", "1d"]),
    "donchian":         (donchian.generate,         ["4h", "1d", "1w"]),
    "ma_cross":         (ma_cross.generate,         ["4h", "1d", "1w"]),
    "breakout_retest":  (breakout_retest.generate,  ["4h", "1d"]),
    "slow_trend":       (slow_trend.generate,       ["1w", "1M"]),
}

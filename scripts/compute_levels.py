"""Compute session levels from data/cache/latest.json.

Outputs per timeframe:
- 50 EMA High (EMA on candle highs) and 50 EMA Low (EMA on candle lows)
- 50 EMA Close (for trend context)
- ATR(14)
- Last swing high and low (fractal: 5-bar pivot)
- Current close vs 50 EMA channel (above / inside / below)

Plus daily-pivot levels from the most recent completed D1 candle (PP, R1, R2, S1, S2),
Previous Day High/Low/Close, and Asia range from M15 00:00-06:00 UTC candles.

Prints a structured summary; also writes data/cache/levels.json.
"""
from __future__ import annotations

import json
from datetime import datetime, time, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache" / "latest.json"
OUT = ROOT / "data" / "cache" / "levels.json"


def ema(values: list[float], period: int) -> list[float]:
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    out = [sum(values[:period]) / period]
    for v in values[period:]:
        out.append(v * k + out[-1] * (1 - k))
    # Pad front with Nones so index aligns with source if caller wants
    return [None] * (period - 1) + out  # type: ignore[list-item]


def atr(candles: list[dict], period: int = 14) -> float | None:
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l = candles[i]["h"], candles[i]["l"]
        pc = candles[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    # Wilder smoothing
    a = sum(trs[:period]) / period
    for tr in trs[period:]:
        a = (a * (period - 1) + tr) / period
    return a


def williams_r(candles: list[dict], period: int = 14) -> float | None:
    if len(candles) < period:
        return None
    recent = candles[-period:]
    hh = max(c["h"] for c in recent)
    ll = min(c["l"] for c in recent)
    close = candles[-1]["c"]
    if hh == ll:
        return None
    return -100.0 * (hh - close) / (hh - ll)


def stochastic(candles: list[dict], k_period: int = 14, k_smooth: int = 3, d_smooth: int = 3) -> tuple[float | None, float | None]:
    """Return (stoch %K smoothed, stoch %D)."""
    n = k_period + k_smooth + d_smooth
    if len(candles) < n:
        return None, None
    raw_k: list[float] = []
    for i in range(k_period - 1, len(candles)):
        window = candles[i - k_period + 1 : i + 1]
        hh = max(c["h"] for c in window)
        ll = min(c["l"] for c in window)
        close = candles[i]["c"]
        raw_k.append(100.0 * (close - ll) / (hh - ll) if hh != ll else 50.0)
    # Smooth %K with SMA(k_smooth)
    k_smoothed = [sum(raw_k[i - k_smooth + 1 : i + 1]) / k_smooth for i in range(k_smooth - 1, len(raw_k))]
    # %D = SMA(d_smooth) of smoothed %K
    d = [sum(k_smoothed[i - d_smooth + 1 : i + 1]) / d_smooth for i in range(d_smooth - 1, len(k_smoothed))]
    return k_smoothed[-1], d[-1]


def find_swings(candles: list[dict], left: int = 2, right: int = 2) -> tuple[float | None, float | None]:
    swing_high = swing_low = None
    n = len(candles)
    for i in range(n - right - 1, left - 1, -1):
        h = candles[i]["h"]
        l = candles[i]["l"]
        if swing_high is None and all(h > candles[i - j]["h"] for j in range(1, left + 1)) and all(
            h > candles[i + j]["h"] for j in range(1, right + 1)
        ):
            swing_high = h
        if swing_low is None and all(l < candles[i - j]["l"] for j in range(1, left + 1)) and all(
            l < candles[i + j]["l"] for j in range(1, right + 1)
        ):
            swing_low = l
        if swing_high is not None and swing_low is not None:
            break
    return swing_high, swing_low


def daily_pivots(d1: list[dict]) -> dict | None:
    # Use the most recent COMPLETED daily candle. If the last one is today (partial), step back.
    if len(d1) < 2:
        return None
    prev = d1[-2]  # previous day is typically fully closed
    h, l, c = prev["h"], prev["l"], prev["c"]
    pp = (h + l + c) / 3
    return {
        "based_on": prev["t"],
        "PP": pp,
        "R1": 2 * pp - l,
        "S1": 2 * pp - h,
        "R2": pp + (h - l),
        "S2": pp - (h - l),
        "PDH": h,
        "PDL": l,
        "PDC": c,
    }


def asia_range(m15: list[dict]) -> dict | None:
    # Asia: 00:00 <= hour < 06:00 UTC on the most recent UTC day that has any M15 data
    if not m15:
        return None
    # Determine "today" UTC by the latest candle timestamp
    last_dt = _parse_dt(m15[-1]["t"])
    if not last_dt:
        return None
    target_date = last_dt.date()
    highs, lows = [], []
    for c in m15:
        dt = _parse_dt(c["t"])
        if not dt or dt.date() != target_date:
            continue
        if time(0, 0) <= dt.time() < time(6, 0):
            highs.append(c["h"])
            lows.append(c["l"])
    if not highs:
        return None
    return {"date": target_date.isoformat(), "high": max(highs), "low": min(lows)}


def _parse_dt(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def analyze_tf(candles: list[dict]) -> dict:
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    closes = [c["c"] for c in candles]
    ema_h = ema(highs, 50)
    ema_l = ema(lows, 50)
    ema_c = ema(closes, 50)
    last_close = closes[-1] if closes else None
    last_ema_h = ema_h[-1] if ema_h and ema_h[-1] is not None else None
    last_ema_l = ema_l[-1] if ema_l and ema_l[-1] is not None else None
    last_ema_c = ema_c[-1] if ema_c and ema_c[-1] is not None else None
    position = None
    if last_close is not None and last_ema_h and last_ema_l:
        if last_close > last_ema_h:
            position = "above_channel"
        elif last_close < last_ema_l:
            position = "below_channel"
        else:
            position = "inside_channel"
    swing_h, swing_l = find_swings(candles)
    stoch_k, stoch_d = stochastic(candles)
    return {
        "last_close": last_close,
        "ema50_high": last_ema_h,
        "ema50_low": last_ema_l,
        "ema50_close": last_ema_c,
        "position_vs_channel": position,
        "atr14": atr(candles, 14),
        "last_swing_high": swing_h,
        "last_swing_low": swing_l,
        "williams_r14": williams_r(candles),
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "last_candle_time": candles[-1]["t"] if candles else None,
    }


def main() -> None:
    if not CACHE.exists():
        raise SystemExit(f"No data at {CACHE}. Run scripts/fetch_gold.py first.")
    data = json.loads(CACHE.read_text())
    tfs = data.get("timeframes", {})

    summary: dict = {
        "fetched_at_utc": data.get("fetched_at_utc"),
        "spot": data.get("spot", {}).get("price"),
        "spot_bid": data.get("spot", {}).get("bid"),
        "spot_ask": data.get("spot", {}).get("ask"),
        "timeframes": {},
    }
    for label in ("D1", "H4", "H1", "M15"):
        tf = tfs.get(label)
        if tf:
            summary["timeframes"][label] = analyze_tf(tf["candles"])

    if "D1" in tfs:
        summary["daily_pivots"] = daily_pivots(tfs["D1"]["candles"])
    if "M15" in tfs:
        summary["asia_range"] = asia_range(tfs["M15"]["candles"])

    OUT.write_text(json.dumps(summary, indent=2, default=str))

    print(f"Spot: {summary['spot']} (bid {summary['spot_bid']} / ask {summary['spot_ask']})")
    for label, a in summary["timeframes"].items():
        print(
            f"[{label}] close={a['last_close']:.2f} "
            f"EMA50H={a['ema50_high'] and round(a['ema50_high'],2)} "
            f"EMA50L={a['ema50_low'] and round(a['ema50_low'],2)} "
            f"pos={a['position_vs_channel']} ATR14={a['atr14'] and round(a['atr14'],2)} "
            f"WR={a['williams_r14'] and round(a['williams_r14'],1)} "
            f"StochK={a['stoch_k'] and round(a['stoch_k'],1)} "
            f"StochD={a['stoch_d'] and round(a['stoch_d'],1)} "
            f"swingH={a['last_swing_high']} swingL={a['last_swing_low']}"
        )
    if summary.get("daily_pivots"):
        p = summary["daily_pivots"]
        print(
            f"Pivots (from {p['based_on']}): PP={p['PP']:.2f} "
            f"R1={p['R1']:.2f} R2={p['R2']:.2f} S1={p['S1']:.2f} S2={p['S2']:.2f} "
            f"PDH={p['PDH']:.2f} PDL={p['PDL']:.2f}"
        )
    if summary.get("asia_range"):
        ar = summary["asia_range"]
        print(f"Asia range ({ar['date']}): H={ar['high']:.2f} L={ar['low']:.2f}")


if __name__ == "__main__":
    main()

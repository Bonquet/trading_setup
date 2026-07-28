from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import monitor_trades  # noqa: E402


class TradeMonitorTests(unittest.TestCase):
    def trade(self, direction: str) -> dict:
        return {
            "id": "test",
            "direction": direction,
            "entry": 4000.0,
            "sl": 4010.0 if direction == "SELL" else 3990.0,
            "tp2": 3980.0 if direction == "SELL" else 4020.0,
            "opened_at": "2026-07-28T12:00:00Z",
        }

    def test_sell_tp_is_detected(self) -> None:
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4002, "l": 3979, "c": 3981}]
        self.assertEqual(
            monitor_trades.candle_outcome(self.trade("SELL"), candles),
            ("win", 3980.0, "2026-07-28T12:05:00Z"),
        )

    def test_buy_sl_is_detected(self) -> None:
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4003, "l": 3989, "c": 3992}]
        self.assertEqual(
            monitor_trades.candle_outcome(self.trade("BUY"), candles),
            ("loss", 3990.0, "2026-07-28T12:05:00Z"),
        )

    def test_pre_entry_candles_are_ignored(self) -> None:
        candles = [
            {"t": "2026-07-28T11:55:00Z", "h": 4011, "l": 3999, "c": 4000},
            {"t": "2026-07-28T12:05:00Z", "h": 4002, "l": 3998, "c": 4001},
        ]
        self.assertIsNone(monitor_trades.candle_outcome(self.trade("SELL"), candles))

    def test_ambiguous_candle_uses_conservative_sl(self) -> None:
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4011, "l": 3979, "c": 4000}]
        self.assertEqual(monitor_trades.candle_outcome(self.trade("SELL"), candles)[0], "loss")

    def test_result_message_is_compact(self) -> None:
        message = monitor_trades.result_message(self.trade("SELL"), "win", 3980.0)
        self.assertEqual(message, "XAUUSD SELL - TP HIT\nEntry: 4000.00\nTP: 3980.00")


if __name__ == "__main__":
    unittest.main()

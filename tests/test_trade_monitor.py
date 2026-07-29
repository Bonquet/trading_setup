from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

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
            "tp1": 3990.0 if direction == "SELL" else 4010.0,
            "tp2": 3980.0 if direction == "SELL" else 4020.0,
            "tp3": 3970.0 if direction == "SELL" else 4030.0,
            "target_hits": {},
            "opened_at": "2026-07-28T12:00:00Z",
        }

    def test_sell_final_tp_is_detected(self) -> None:
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4002, "l": 3969, "c": 3971}]
        self.assertEqual(
            monitor_trades.candle_outcome(self.trade("SELL"), candles),
            ("win", 3970.0, "2026-07-28T12:05:00Z"),
        )
        events = monitor_trades.candle_events(self.trade("SELL"), candles)
        self.assertEqual([event["name"] for event in events], ["TP1", "TP2", "TP3"])

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
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4011, "l": 3969, "c": 4000}]
        self.assertEqual(monitor_trades.candle_outcome(self.trade("SELL"), candles)[0], "loss")

    def test_intermediate_target_does_not_close_trade(self) -> None:
        candles = [{"t": "2026-07-28T12:05:00Z", "h": 4002, "l": 3989, "c": 3991}]
        self.assertIsNone(monitor_trades.candle_outcome(self.trade("SELL"), candles))
        self.assertEqual(
            [event["name"] for event in monitor_trades.candle_events(self.trade("SELL"), candles)],
            ["TP1"],
        )

    def test_recorded_target_is_not_repeated(self) -> None:
        trade = self.trade("SELL")
        trade["target_hits"] = {
            "tp1": {"name": "TP1", "price": 3990.0, "notified_at": "2026-07-28T12:06Z"}
        }
        candles = [{"t": "2026-07-28T12:10:00Z", "h": 4002, "l": 3979, "c": 3981}]
        self.assertEqual(
            [event["name"] for event in monitor_trades.candle_events(trade, candles)],
            ["TP2"],
        )

    def test_target_message_is_compact(self) -> None:
        message = monitor_trades.target_message(self.trade("SELL"), "TP2", 3980.0)
        self.assertEqual(message, "XAUUSD SELL - TP2 HIT\nEntry: 4000.00\nTP2: 3980.00")

    def test_closing_one_trade_leaves_the_other_open(self) -> None:
        first = self.trade("SELL")
        first.update({"lots": 0.01, "risk_usd": 10.0, "account": "main"})
        second = deepcopy(first)
        second["id"] = "second"
        data = {
            "accounts": {"main": {"balance": 1000.0}},
            "open": [first, second],
            "closed": [],
        }
        monitor_trades.close_trade(
            data, first, "win", 3970.0, "2026-07-28T13:00:00Z", final_level="TP3"
        )
        self.assertEqual([trade["id"] for trade in data["open"]], ["second"])

    @patch("monitor_trades.subprocess.run")
    def test_distinct_signals_get_distinct_target_notifications(self, run_mock) -> None:
        run_mock.return_value.returncode = 0
        first = self.trade("SELL")
        first.update({"signal_id": "one", "target_hits": {
            "tp1": {"name": "TP1", "price": 3990.0, "notified_at": None}
        }})
        second = deepcopy(first)
        second.update({"id": "second", "signal_id": "two", "entry": 3995.0})
        data = {"open": [first, second], "closed": []}
        self.assertEqual(monitor_trades.notify_pending(data), 2)
        self.assertEqual(run_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()

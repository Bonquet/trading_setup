from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_signal  # noqa: E402
import run_auto  # noqa: E402


class SignalTargetTests(unittest.TestCase):
    def test_swing_sell_uses_one_two_and_final_r_targets(self) -> None:
        tp1, tp2, tp3, final_tp, pivot = generate_signal.build_targets(
            "SELL",
            4000.0,
            10.0,
            "pivot_or_25r",
            {"S2": 3966.0},
        )
        self.assertEqual((tp1, tp2, tp3, final_tp, pivot), (3990.0, 3980.0, 3966.0, 3966.0, 3966.0))

    def test_scalp_has_two_targets(self) -> None:
        targets = generate_signal.build_targets("BUY", 4000.0, 10.0, "fixed_15r", {})
        self.assertEqual(targets, (4010.0, 4015.0, None, 4015.0, None))

    def test_public_signal_lists_all_targets_without_explanation(self) -> None:
        message = run_auto.build_telegram_signal({
            "direction": "SELL",
            "entry": 4000.0,
            "stop_loss": 4010.0,
            "tp1": 3990.0,
            "tp2": 3980.0,
            "tp3": 3975.0,
        })
        self.assertEqual(
            message,
            "XAUUSD SELL @ 4000.00\nSL: 4010.00\n"
            "TP1: 3990.00\nTP2: 3980.00\nTP3: 3975.00",
        )


if __name__ == "__main__":
    unittest.main()

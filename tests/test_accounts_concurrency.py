from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import accounts  # noqa: E402


class AccountsConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_state = accounts.STATE
        accounts.STATE = Path(self.temp_dir.name) / "accounts.json"
        accounts.save({
            "active": "main",
            "accounts": {
                "main": {
                    "balance": 1000.0,
                    "risk_pct": 1.0,
                    "max_concurrent_trades": 2,
                }
            },
            "open": [],
            "closed": [],
        })

    def tearDown(self) -> None:
        accounts.STATE = self.original_state
        self.temp_dir.cleanup()

    def open_trade(self, signal_id: str, setup_key: str, entry: float) -> str:
        return accounts.cmd_open(
            "main",
            "SELL",
            entry,
            entry + 10,
            entry - 10,
            entry - 20,
            "50 EMA Williams (swing)",
            1.0,
            lots=0.01,
            risk_usd=10.0,
            signal_id=signal_id,
            tp3=entry - 25,
            setup_key=setup_key,
        )

    def test_two_distinct_trades_are_allowed_and_third_is_refused(self) -> None:
        self.assertTrue(self.open_trade("signal-1", "setup-1", 4000).startswith("Opened #"))
        self.assertTrue(self.open_trade("signal-2", "setup-2", 3995).startswith("Opened #"))
        self.assertTrue(self.open_trade("signal-3", "setup-3", 3990).startswith("REFUSED:"))
        state = json.loads(accounts.STATE.read_text(encoding="utf-8"))
        self.assertEqual(len(state["open"]), 2)
        self.assertEqual(len({trade["id"] for trade in state["open"]}), 2)

    def test_same_setup_is_not_opened_twice(self) -> None:
        self.open_trade("signal-1", "setup-1", 4000)
        duplicate = self.open_trade("signal-2", "setup-1", 3999)
        self.assertEqual(duplicate, "Already recorded: setup setup-1.")
        self.assertEqual(len(accounts.load()["open"]), 1)

    def test_close_requires_trade_id_when_multiple_are_open(self) -> None:
        self.open_trade("signal-1", "setup-1", 4000)
        self.open_trade("signal-2", "setup-2", 3995)
        self.assertIn("Multiple trades are open", accounts.cmd_close("win"))
        first_id = accounts.load()["open"][0]["id"]
        self.assertIn("Closed:", accounts.cmd_close("win", trade_id=first_id))
        self.assertEqual(len(accounts.load()["open"]), 1)


if __name__ == "__main__":
    unittest.main()

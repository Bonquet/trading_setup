from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import accounts
import generate_signal
import monitor_trades
import run_auto
from signal_grading import GRADING_VERSION, grade_momentum


class GradingTests(unittest.TestCase):
    def test_swing_sell_all_score_levels(self):
        cfg = generate_signal.STYLES["swing"]
        for wr, k, d, score, grade in [
            (-85.3, 12, 14.3, 1, "A"),  # Screenshot's stored indicators.
            (-85, 30, 32, 0, "A"),
            (-95, 15, 17, 2, "A+"),
            (-95, 15, 20, 3, "S"),
        ]:
            with self.subTest(grade=grade, score=score):
                result = grade_momentum("SELL", wr, k, d, cfg)
                self.assertEqual((result["grade_score"], result["setup_grade"]), (score, grade))
                self.assertEqual(result["grading_version"], GRADING_VERSION)

    def test_buy_and_sell_are_symmetric_for_every_style(self):
        for cfg in generate_signal.STYLES.values():
            for wr, k, d in [(-1, 99, 90), (-15, 70, 68), (-5, 85, 83)]:
                buy = grade_momentum("BUY", wr, k, d, cfg)
                sell = grade_momentum("SELL", -100 - wr, 100 - k, 100 - d, cfg)
                self.assertEqual(buy["setup_grade"], sell["setup_grade"])
                self.assertEqual(buy["grade_score"], sell["grade_score"])

    def test_threshold_boundaries_and_raw_precision(self):
        cfg = generate_signal.STYLES["swing"]
        equal = grade_momentum("BUY", -10, 80, 75, cfg)
        self.assertEqual(equal["grade_score"], 1)
        beyond = grade_momentum("BUY", -9.999, 80.001, 75, cfg)
        self.assertEqual(beyond["setup_grade"], "S")

    def test_engine_assigns_grade_only_after_existing_gates(self):
        # No provider requests, notifications, or real state writes.
        with tempfile.TemporaryDirectory() as td:
            levels, out = Path(td) / "levels.json", Path(td) / "signal.json"
            tf = {"position_vs_channel": "below_channel", "williams_r14": -95,
                  "stoch_k": 15, "stoch_d": 21, "last_close": 4000,
                  "last_swing_high": 4010, "last_swing_low": 3990, "atr14": 10}
            payload = {"spot": 4000, "timeframes": {"H4": tf, "D1": dict(tf), "H1": dict(tf)}}
            with patch.object(generate_signal, "LEVELS", levels), patch.object(generate_signal, "OUT", out), \
                 patch.object(sys, "argv", ["generate_signal.py", "1000", "0.01", "0", "--style=swing"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                levels.write_text(json.dumps(payload))
                generate_signal.main()
                result = json.loads(out.read_text())
                self.assertEqual(result["setup_grade"], "S")
                # Grading does not change generated prices or lot sizing.
                self.assertEqual((result["entry"], result["stop_loss"], result["tp3"], result["lots"]),
                                 (4000, 4015, 3962.5, 0.01))
                tf["williams_r14"] = -79
                levels.write_text(json.dumps(payload))
                with self.assertRaises(SystemExit) as stop:
                    generate_signal.main()
                self.assertEqual(stop.exception.code, 10)
                self.assertNotIn("setup_grade", json.loads(out.read_text()))

    def test_grade_survives_tracking_and_closure_and_updates_repeat_signal(self):
        with tempfile.TemporaryDirectory() as td, patch.object(accounts, "STATE", Path(td) / "accounts.json"):
            accounts.save({"active": "main", "accounts": {"main": {"balance": 1000, "risk_pct": 1}},
                           "open": [], "closed": []})
            grading = grade_momentum("SELL", -95, 15, 21, generate_signal.STYLES["swing"])
            accounts.cmd_open("main", "SELL", 4000, 4010, 3990, 3980, "50 EMA Williams (swing)", 1,
                              lots=0.01, risk_usd=10, signal_id="unique-signal", tp3=3975, grading=grading)
            data = accounts.load()
            trade = data["open"][0]
            for key, value in grading.items():
                self.assertEqual(trade[key], value)
            original = run_auto.build_telegram_signal(dict(trade, stop_loss=trade["sl"]))
            self.assertIn("Grade: S", original)
            self.assertIn("Signal: unique-signal", original)
            for name, price in [("TP1", 3990), ("TP2", 3980), ("TP3", 3975)]:
                self.assertEqual(monitor_trades.target_message(trade, name, price),
                                 f"{original}\n\n{name} HIT\nHit price: {price:.2f}")
            self.assertTrue(monitor_trades.result_message(trade, "loss", 4010).startswith(original + "\n\nSL HIT"))
            closed = monitor_trades.close_trade(data, trade, "win", 3975, "2026-11-18T12:00:00Z", "TP3")
            self.assertEqual(closed["grade_checks"], grading["grade_checks"])
            self.assertEqual(closed["setup_grade"], "S")

    def test_legacy_scalp_update_has_no_invented_grade_or_tp3(self):
        trade = {"direction": "BUY", "entry": 4000, "sl": 3990, "tp1": 4010, "tp2": 4015,
                 "tp3": None, "signal_id": "legacy"}
        msg = monitor_trades.result_message(trade, "win", 4015)
        self.assertNotIn("Grade:", msg)
        self.assertNotIn("TP3", msg)
        self.assertIn("TP2 HIT (FINAL TP)", msg)
        self.assertIn("Signal: legacy", msg)

    def test_runner_publishes_and_tracks_the_same_grade_and_reference(self):
        grading = grade_momentum("SELL", -95, 15, 21, generate_signal.STYLES["swing"])
        sig = dict(grading, decision="Valid Trade", direction="SELL", entry=4000,
                   stop_loss=4010, tp1=3990, tp2=3980, tp3=3975, final_tp=3975,
                   strategy="50 EMA Williams (swing)", style="swing", lots=0.01,
                   risk_usd=10, account=1000, rr_to_final=2.5, setup_key="test-setup",
                   confluence={"williams_r14": -95, "stoch_k": 15, "stoch_d": 21})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "signal.json"
            path.write_text(json.dumps(sig))
            with patch.object(run_auto, "SIGNAL", path), \
                 patch.object(run_auto, "resolve_account", return_value=("main", {"balance": 1000})), \
                 patch.object(run_auto, "current_xau_trades", return_value=[]), \
                 patch.object(run_auto, "run", return_value=0), \
                 patch.object(run_auto, "new_signal_id", return_value="stable-reference"), \
                 patch.object(accounts, "cmd_open", return_value="Opened #test") as opened, \
                 patch.object(run_auto, "publish_signal_for_ea") as published, \
                 patch.object(run_auto, "append_journal"), \
                 patch.object(run_auto.subprocess, "run") as notify, \
                 patch.object(sys, "argv", ["run_auto.py", "ny", "1000"]), \
                 contextlib.redirect_stdout(io.StringIO()):
                notify.return_value.returncode = 0
                run_auto.main()
                self.assertEqual(opened.call_args.kwargs["grading"], grading)
                self.assertEqual(opened.call_args.kwargs["signal_id"], "stable-reference")
                self.assertEqual(published.call_args.args[0]["setup_grade"], "S")
                self.assertEqual(published.call_args.args[0]["signal_id"], "stable-reference")
                telegram_message = notify.call_args_list[-1].args[0][-1]
                self.assertIn("Grade: S", telegram_message)
                self.assertIn("Signal: stable-reference", telegram_message)


if __name__ == "__main__":
    unittest.main()

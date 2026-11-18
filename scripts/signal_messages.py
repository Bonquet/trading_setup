"""One signal block shared by initial alerts and target/stop updates."""
from __future__ import annotations


def signal_message(signal: dict) -> str:
    stop = signal["stop_loss"] if "stop_loss" in signal else signal["sl"]
    lines = [f"XAUUSD {signal['direction']} @ {float(signal['entry']):.2f}"]
    if signal.get("setup_grade"):
        lines.append(f"Grade: {signal['setup_grade']}")
    lines.append(f"SL: {float(stop):.2f}")
    for name in ("tp1", "tp2", "tp3"):
        if signal.get(name) is not None:
            lines.append(f"{name.upper()}: {float(signal[name]):.2f}")
    reference = signal.get("signal_id") or signal.get("id")
    if reference:
        lines.append(f"Signal: {reference}")
    return "\n".join(lines)

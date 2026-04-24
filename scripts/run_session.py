"""Full session orchestrator.

Usage:
  python scripts/run_session.py london
  python scripts/run_session.py ny

Steps:
  1. Run fetch_gold.py   -> data/cache/latest.json
  2. Run compute_levels.py -> data/cache/levels.json
  3. Print a concise session header the analyst (Claude) will build the brief from.

The brief itself is produced by Claude in the session using strategy/playbook.md.
If you want the notifier to fire, call scripts/notify_whatsapp.py separately
after Claude gives you a Valid Trade decision (do NOT spam every run).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(ROOT))
    if r.returncode != 0:
        sys.exit(r.returncode)


def main() -> None:
    session = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if session not in ("london", "ny"):
        sys.exit("Usage: python scripts/run_session.py <london|ny>")

    print(f"=== {session.upper()} session — preparing data ===")
    run([sys.executable, str(SCRIPTS / "fetch_gold.py")])
    run([sys.executable, str(SCRIPTS / "compute_levels.py")])
    print("\nData ready. Load strategy/playbook.md and routines/" + session + ".md, then produce the brief.")


if __name__ == "__main__":
    main()

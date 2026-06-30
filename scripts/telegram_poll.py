"""Telegram command listener (polling).

Reads messages you send to the bot via getUpdates, runs the SAME commands as the
WhatsApp dispatcher, and replies in the Telegram chat. Designed to be invoked on a
schedule by .github/workflows/telegram-command.yml (or run locally for testing).

Security: only messages from TELEGRAM_CHAT_ID (the authorized user) are acted on.
Anything else is skipped (but the offset still advances so it is not reprocessed).

State: the last processed update_id+1 is stored in data/telegram_offset.json and
committed by the workflow so commands are never run twice.

Commands (mirror of the WhatsApp set):
  /health /london /ny /best [high] /scalp /quick /current /summary
  /accounts /balance /active /risk /buffer /maxrisk /style
  /took /close /pnl /freeze /unfreeze /resetphase /help

Usage:
  python scripts/telegram_poll.py            # one polling batch
  python scripts/telegram_poll.py --timeout 0
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ENV_PATH = ROOT / "config" / ".env"
OFFSET_PATH = ROOT / "data" / "telegram_offset.json"
API = "https://api.telegram.org/bot{token}/{method}"

ACCOUNT_CMDS = {
    "accounts", "balance", "active", "risk", "buffer", "maxrisk",
    "style", "took", "close", "pnl", "freeze", "unfreeze", "resetphase",
}
HELP_TEXT = (
    "Commands: /health /london /ny /best /scalp /quick /current /summary "
    "/accounts /balance /active /risk /buffer /maxrisk /style /took /close "
    "/pnl /freeze /unfreeze /help"
)


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            if " #" in v and not (v.startswith('"') or v.startswith("'")):
                v = v.split(" #", 1)[0].strip()
            env[k.strip()] = v
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def get_updates(token: str, offset: int | None, timeout: int) -> list[dict]:
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    url = API.format(token=token, method="getUpdates") + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=timeout + 15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        # 409 = a webhook is active, so polling is intentionally disabled. The
        # webhook is the live path; treat this as "nothing to poll" and exit clean
        # so the 5-min fallback cron doesn't spam failed runs.
        if e.code == 409:
            print("Webhook active — polling disabled (handled by webhook). Nothing to do.")
            return []
        raise SystemExit(f"HTTP {e.code} from getUpdates\n{body}") from e
    if not data.get("ok"):
        raise SystemExit(f"getUpdates not ok: {data}")
    return data.get("result", [])


def read_offset() -> int | None:
    if OFFSET_PATH.exists():
        try:
            return int(json.loads(OFFSET_PATH.read_text()).get("offset"))
        except Exception:  # noqa: BLE001
            return None
    return None


def write_offset(offset: int) -> None:
    OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_PATH.write_text(json.dumps({"offset": offset}, indent=2))


def child_env(env: dict) -> dict:
    """Env for dispatched commands: route ALL replies to Telegram and silence WhatsApp."""
    e = os.environ.copy()
    e["NOTIFIER_SCRIPT"] = "notify_telegram.py"  # accounts/health/weekly reply via Telegram
    e["WHATSAPP_BACKEND"] = "disabled"           # run_auto won't double-post to WhatsApp
    e["ON_DEMAND"] = "1"                          # always reply, even on No Trade
    e["TELEGRAM_BOT_TOKEN"] = env.get("TELEGRAM_BOT_TOKEN", "")
    e["TELEGRAM_CHAT_ID"] = env.get("TELEGRAM_CHAT_ID", "")
    return e


def reply(text: str, env: dict) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPTS / "notify_telegram.py"), text],
        cwd=str(ROOT), check=False, env=child_env(env),
    )


def run(cmd: list[str], env: dict, extra: dict | None = None) -> None:
    e = child_env(env)
    if extra:
        e.update(extra)
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=str(ROOT), env=e, check=False)


def dispatch(cmd: str, args: str, env: dict) -> None:
    py = sys.executable
    cmd = cmd.lower()
    if cmd == "health":
        run([py, str(SCRIPTS / "health_check.py"), "--notify"], env)
    elif cmd == "london":
        run([py, str(SCRIPTS / "run_auto.py"), "london", "10000"], env)
    elif cmd == "ny":
        run([py, str(SCRIPTS / "run_auto.py"), "ny", "10000"], env)
    elif cmd == "best":
        extra = {"HIGH_CONVICTION": "1"} if args.lower() in ("high", "aggressive") else None
        run([py, str(SCRIPTS / "run_auto.py"), "manual", "10000"], env, extra)
    elif cmd in ("scalp", "quick"):
        run([py, str(SCRIPTS / "run_auto.py"), "manual-scalp", "10000"], env,
            {"STYLE_OVERRIDE": "scalp"})
    elif cmd == "summary":
        run([py, str(SCRIPTS / "weekly_stats.py"), "--days", "7", "--notify"], env)
    elif cmd == "current":
        if subprocess.run([py, str(SCRIPTS / "fetch_gold.py")], cwd=str(ROOT),
                          env=child_env(env)).returncode != 0:
            reply("XAU /current failed: price refresh failed. Not using stale cache.", env)
            return
        if subprocess.run([py, str(SCRIPTS / "compute_levels.py")], cwd=str(ROOT),
                          env=child_env(env)).returncode != 0:
            reply("XAU /current failed: level computation failed.", env)
            return
        run([py, str(SCRIPTS / "accounts.py"), "whatsapp", cmd, args], env)
    elif cmd in ACCOUNT_CMDS:
        run([py, str(SCRIPTS / "accounts.py"), "whatsapp", cmd, args], env)
    elif cmd == "start":
        reply("\U0001F44B XAUUSD bot connected. You can now send commands here.\n\n" + HELP_TEXT, env)
    elif cmd in ("help", ""):
        reply(HELP_TEXT, env)
    else:
        reply(f"Unknown command: /{cmd} — try /help", env)


def parse_command(text: str) -> tuple[str, str]:
    """'/took acct1 0.5' -> ('took', 'acct1 0.5'). Strips @botname."""
    text = text.strip()
    if not text.startswith("/"):
        return "", ""
    parts = text[1:].split(maxsplit=1)
    cmd = parts[0].split("@", 1)[0].lower()  # /london@tradekanashibot -> london
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=20, help="long-poll seconds (0 = immediate)")
    ap.add_argument("--text", type=str, default=None,
                    help="webhook mode: dispatch this single command now (no polling)")
    a = ap.parse_args()

    env = load_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    auth_chat = str(env.get("TELEGRAM_CHAT_ID", "")).strip()
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN required in config/.env or env")
    if not auth_chat:
        sys.exit("TELEGRAM_CHAT_ID required (authorized user) in config/.env or env")

    # Webhook (instant) mode: dispatch the one command passed in and exit.
    if a.text:
        cmd, args = parse_command(a.text)
        if not cmd:
            print("No command in --text; nothing to do.")
            return
        print(f"Webhook dispatch /{cmd} args='{args}'")
        dispatch(cmd, args, env)
        return

    offset = read_offset()
    updates = get_updates(token, offset, a.timeout)
    if not updates:
        print("No new messages.")
        return

    last_update_id = offset - 1 if offset else 0
    processed = 0
    for upd in updates:
        last_update_id = max(last_update_id, upd["update_id"])
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text", "")
        if chat_id != auth_chat:
            print(f"Skipping message from unauthorized chat {chat_id}.")
            continue
        if not text.startswith("/"):
            continue
        cmd, args = parse_command(text)
        print(f"Dispatching /{cmd} args='{args}'")
        try:
            dispatch(cmd, args, env)
            processed += 1
        except Exception as e:  # noqa: BLE001
            print(f"(dispatch /{cmd} failed: {e})")
            reply(f"/{cmd} failed: {e}", env)

    write_offset(last_update_id + 1)
    print(f"Processed {processed} command(s). New offset {last_update_id + 1}.")


if __name__ == "__main__":
    main()

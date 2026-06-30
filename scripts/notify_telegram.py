"""Send a Telegram message via the Bot API.

Unlike WhatsApp, Telegram has NO 24-hour window: once the user presses Start
on the bot, the bot can message them any time, for free, with no re-activation.

Config (config/.env, overlaid by os.environ so CI secrets win):
  TELEGRAM_BOT_TOKEN   from @BotFather
  TELEGRAM_CHAT_ID     your numeric chat id (auto-filled by --setup)

Usage:
  python scripts/notify_telegram.py "your message body"
  echo "msg" | python scripts/notify_telegram.py -
  python scripts/notify_telegram.py --setup     # detect & save chat id
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "config" / ".env"
API = "https://api.telegram.org/bot{token}/{method}"


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


def http(token: str, method: str, params: dict) -> dict:
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} from {method}\n{body}") from e


def get_updates(token: str) -> dict:
    url = API.format(token=token, method="getUpdates")
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} from getUpdates\n{body}") from e


def save_chat_id(chat_id: str) -> None:
    """Write/replace TELEGRAM_CHAT_ID line in config/.env."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out, found = [], False
    for line in lines:
        if line.strip().startswith("TELEGRAM_CHAT_ID="):
            out.append(f"TELEGRAM_CHAT_ID={chat_id}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"TELEGRAM_CHAT_ID={chat_id}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def setup(token: str) -> None:
    """Detect chat id from the most recent message sent to the bot."""
    data = get_updates(token)
    results = data.get("result", [])
    if not results:
        sys.exit(
            "No messages found. Open the bot in Telegram and press Start "
            "(or send any message), then run --setup again."
        )
    chat = None
    for upd in reversed(results):
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat")
        if chat:
            break
    if not chat:
        sys.exit("Could not read a chat from updates. Send the bot a message and retry.")
    chat_id = str(chat["id"])
    save_chat_id(chat_id)
    name = chat.get("first_name") or chat.get("title") or chat.get("username") or "?"
    print(f"Saved TELEGRAM_CHAT_ID={chat_id} (chat: {name})")


def main() -> None:
    env = load_env(ENV_PATH)
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        sys.exit("Telegram: TELEGRAM_BOT_TOKEN required in config/.env")

    args = sys.argv[1:]
    if args and args[0] == "--setup":
        setup(token)
        return

    if not args:
        sys.exit('Usage: python scripts/notify_telegram.py "message"  |  --setup')
    message = sys.stdin.read() if args[0] == "-" else args[0]

    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        sys.exit("Telegram: TELEGRAM_CHAT_ID missing. Run: python scripts/notify_telegram.py --setup")

    resp = http(token, "sendMessage", {"chat_id": chat_id, "text": message})
    if not resp.get("ok"):
        sys.exit(f"Telegram send failed: {resp}")
    print("Telegram: sent.")


if __name__ == "__main__":
    main()

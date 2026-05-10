"""Send a WhatsApp message via one of three backends.

Backend selected by WHATSAPP_BACKEND env var in config/.env:
  callmebot  — free, personal number only, NOT groups
  greenapi   — unofficial, supports GROUPS (recommended for group signals)
  twilio     — official, 1-to-1 business messaging, not group-friendly
  disabled   — no-op

Usage:
  python scripts/notify_whatsapp.py "your message body"
  echo "msg" | python scripts/notify_whatsapp.py -
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from base64 import b64encode
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "config" / ".env"


def load_env(path: Path) -> dict[str, str]:
    """Load .env (if present) then overlay os.environ so GitHub Actions secrets win."""
    import os
    env: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip()
            # Strip inline comments: anything after " #" (space+hash) that isn't inside quotes
            if " #" in v and not (v.startswith('"') or v.startswith("'")):
                v = v.split(" #", 1)[0].strip()
            env[k.strip()] = v
    for k in (
        "GOLDAPI_NET_KEY", "QUOTE_SOURCE", "GOLDAPI_KEY", "TWELVEDATA_KEY", "WHATSAPP_BACKEND",
        "CALLMEBOT_PHONE", "CALLMEBOT_APIKEY",
        "GREENAPI_INSTANCE_ID", "GREENAPI_TOKEN", "GREENAPI_GROUP_ID",
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET",
        "TWILIO_FROM", "TWILIO_TO",
        "TWILIO_CONTENT_SID", "TWILIO_CONTENT_VARIABLES",
    ):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def http_request(url: str, *, data: bytes | None = None, headers: dict | None = None, method: str = "GET") -> str:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} from {url}\n{body}") from e


# --- Backends ---

def send_callmebot(env: dict, message: str) -> str:
    phone = env.get("CALLMEBOT_PHONE", "")
    key = env.get("CALLMEBOT_APIKEY", "")
    if not phone or not key:
        sys.exit("CallMeBot: CALLMEBOT_PHONE and CALLMEBOT_APIKEY required in config/.env")
    q = urllib.parse.urlencode({"phone": phone, "text": message, "apikey": key})
    return http_request(f"https://api.callmebot.com/whatsapp.php?{q}")


def send_greenapi(env: dict, message: str) -> str:
    iid = env.get("GREENAPI_INSTANCE_ID", "")
    token = env.get("GREENAPI_TOKEN", "")
    chat = env.get("GREENAPI_GROUP_ID", "")
    if not (iid and token and chat):
        sys.exit("Green API: GREENAPI_INSTANCE_ID, GREENAPI_TOKEN, GREENAPI_GROUP_ID required")
    url = f"https://api.green-api.com/waInstance{iid}/sendMessage/{token}"
    body = json.dumps({"chatId": chat, "message": message}).encode("utf-8")
    return http_request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")


def send_twilio(env: dict, message: str) -> str:
    """Send via Twilio WhatsApp.

    If TWILIO_CONTENT_SID is set, use template messaging (works outside 24h window).
    TWILIO_CONTENT_VARIABLES must be a JSON string, e.g. '{"1":"BUY 2346.5","2":"SL 2338"}'.
    If not set, send as freeform Body (only works within 24h of recipient's last message).
    """
    sid = env.get("TWILIO_ACCOUNT_SID", "")
    api_key_sid = env.get("TWILIO_API_KEY_SID", "")
    api_key_secret = env.get("TWILIO_API_KEY_SECRET", "")
    tok = env.get("TWILIO_AUTH_TOKEN", "")
    frm = env.get("TWILIO_FROM", "")
    to = env.get("TWILIO_TO", "")
    content_sid = env.get("TWILIO_CONTENT_SID", "")
    content_vars = env.get("TWILIO_CONTENT_VARIABLES", "")

    if not (sid and frm and to):
        sys.exit("Twilio: TWILIO_ACCOUNT_SID, TWILIO_FROM, TWILIO_TO required")
    # Prefer API-Key auth (recommended); fall back to raw Account Auth Token.
    if api_key_sid and api_key_secret:
        auth_user, auth_pass = api_key_sid, api_key_secret
    elif tok:
        auth_user, auth_pass = sid, tok
    else:
        sys.exit("Twilio: provide TWILIO_API_KEY_SID+TWILIO_API_KEY_SECRET, or TWILIO_AUTH_TOKEN")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    fields = {"From": frm, "To": to}
    if content_sid:
        fields["ContentSid"] = content_sid
        if content_vars:
            fields["ContentVariables"] = content_vars
    else:
        fields["Body"] = message

    data = urllib.parse.urlencode(fields).encode("utf-8")
    auth = b64encode(f"{auth_user}:{auth_pass}".encode()).decode()
    return http_request(
        url,
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )


BACKENDS = {"callmebot": send_callmebot, "greenapi": send_greenapi, "twilio": send_twilio}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('Usage: python scripts/notify_whatsapp.py "message"  (or use "-" for stdin)')
    message = sys.stdin.read() if sys.argv[1] == "-" else " ".join(sys.argv[1:])
    message = message.strip()
    if not message:
        sys.exit("Empty message")

    env = load_env(ENV_PATH)
    backend = env.get("WHATSAPP_BACKEND", "disabled").lower()
    if backend == "disabled":
        print("WhatsApp notifier disabled (WHATSAPP_BACKEND=disabled). Message was:")
        print(message)
        return
    fn = BACKENDS.get(backend)
    if not fn:
        sys.exit(f"Unknown WHATSAPP_BACKEND={backend}. Use one of: {', '.join(BACKENDS)} | disabled")
    print(fn(env, message))


if __name__ == "__main__":
    main()

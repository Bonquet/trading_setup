# Instant Telegram commands — webhook setup

By default the Telegram listener polls every ~5 minutes (and GitHub often delays
those runs). This webhook makes commands **instant**: Telegram → Cloudflare Worker →
GitHub `repository_dispatch` → the workflow runs immediately. Same idea as the old
WhatsApp + Twilio setup. The 5-minute poll stays on as a safety net.

You do steps 1–3 (they need your accounts/logins); I'll do step 4 (set the webhook).

## 1. Create a GitHub token

GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**
- **Repository access:** Only select repositories → `Bonquet/trading_setup`
- **Permissions:** Repository permissions → **Contents: Read and write** (this is what
  lets it fire `repository_dispatch`)
- Generate, copy the token (starts with `github_pat_…`). You'll paste it into Cloudflare.

## 2. Deploy the Cloudflare Worker (free)

1. Create a free account at https://dash.cloudflare.com (if you don't have one).
2. **Workers & Pages → Create → Create Worker** → name it e.g. `telegram-trade-relay` → Deploy.
3. **Edit code** → delete the sample → paste the contents of
   `cloudflare/telegram-webhook-worker.js` from this repo → **Deploy**.
4. **Settings → Variables and Secrets** → add these (use "Encrypt"/Secret for the token):
   - `GITHUB_TOKEN` = your token from step 1
   - `GITHUB_OWNER` = `Bonquet`
   - `GITHUB_REPO` = `trading_setup`
   - `AUTHORIZED_CHAT_ID` = `5886177468`
   - `WEBHOOK_SECRET` = make up a long random string (e.g. 32+ chars) — keep it; I need it for step 4
5. Copy your Worker URL — it looks like `https://telegram-trade-relay.<your-subdomain>.workers.dev`

## 3. Send me

- the **Worker URL**
- the **WEBHOOK_SECRET** you chose

## 4. I set the Telegram webhook

I'll call Telegram's `setWebhook` pointing at your Worker URL with the secret, so every
message you send the bot is pushed there instantly. After that, `/london`, `/ny`,
`/best`, `/took`, etc. respond within a couple seconds — no more 5-minute wait.

## Notes

- Cloudflare Workers free tier = 100,000 requests/day — far more than enough.
- If you ever rotate the bot token (@BotFather `/revoke`) you'll re-run step 4.
- To temporarily disable the webhook and fall back to polling, delete it via
  `deleteWebhook` (I can do that), and the 5-min schedule keeps working.

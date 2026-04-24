# Enabling slash commands from WhatsApp

When you text `/health`, `/london`, `/ny`, `/best`, or `/summary` to the Twilio WhatsApp number, the bot should run it and text back the result. This one-time setup wires Twilio's inbound webhook → a Twilio Function → GitHub Actions → WhatsApp reply.

Architecture:

```
You text "/health" to Twilio WhatsApp number
   ↓
Twilio hits the Function's URL (Inbound URL on the sandbox)
   ↓
Function parses the word, POSTs repository_dispatch to GitHub
   ↓
Function replies to you: "/health queued — result in ~30s"
   ↓
GitHub Actions runs .github/workflows/whatsapp-command.yml
   ↓
The workflow's script sends the actual result via Twilio outbound
```

## One-time deploy (5 minutes)

### Step 1 — Create a GitHub fine-grained Personal Access Token

1. Go to https://github.com/settings/personal-access-tokens/new
2. **Token name**: `twilio-whatsapp-inbound`
3. **Expiration**: 1 year (or "No expiration" if your account allows)
4. **Repository access**: *Only select repositories* → pick `Bonquet/trading_setup`
5. **Repository permissions**:
   - **Actions**: Read and **Write**
   - **Contents**: Read
6. Click **Generate token** — copy the `github_pat_...` value (you will paste it into Twilio next; you won't see it again)

### Step 2 — Deploy the Twilio Function

1. Open https://console.twilio.com/us1/develop/functions/services
2. Click **Create Service** → name it `xau-bot` → Next
3. In the Service, click **Add** → **Add Function**:
   - **Path**: `/whatsapp-inbound`
   - **Visibility**: Public
4. Open `twilio/whatsapp-inbound.js` from this repo, copy the entire contents, paste into the Twilio Function editor (replacing the default code)
5. Click **Save**
6. Left sidebar → **Environment Variables** → add three:
   - `GH_OWNER` = `Bonquet`
   - `GH_REPO` = `trading_setup`
   - `GH_TOKEN` = *(the `github_pat_...` from Step 1)*
7. Click **Deploy All** (top-right). Wait for the green "Deployment successful" toast.
8. Back on the Function page, copy its **Copy URL** — it looks like:
   `https://xau-bot-####-dev.twil.io/whatsapp-inbound`

### Step 3 — Point the WhatsApp sandbox at the Function

1. Open https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Scroll to **Sandbox Configuration**
3. In **WHEN A MESSAGE COMES IN**, paste the Function URL from Step 2. Method: **HTTP POST**
4. (Leave **Status Callback URL** blank.)
5. Click **Save**

### Step 4 — Test

From the WhatsApp number you have joined the sandbox from, send:

```
/help
```

Expected within seconds: a reply listing the five commands.

Then try:

```
/health
```

Expected:
1. Immediate reply: `/health queued — result in ~30s`
2. Within ~30 seconds: a second message with the health summary (OK/FAIL per check)

## If something doesn't work

| Symptom | Likely cause | Fix |
|---|---|---|
| Twilio echoes "You said: /health. Configure your WhatsApp Sandbox's Inbound URL…" | Step 3 not saved, or URL wrong | Re-paste Function URL in sandbox config |
| "/health queued" but no second message | GH_TOKEN invalid / wrong scopes | Regenerate PAT with Actions:write + Contents:read |
| Immediate reply "failed to queue (HTTP 404)" | GH_OWNER or GH_REPO wrong | Check env vars in Function service |
| Immediate reply "failed to queue (HTTP 401)" | GH_TOKEN expired | Issue new PAT, update env var |
| No reply at all, silent | Twilio sandbox 24h window expired for your phone | Re-send the join phrase to `+1 415 523 8886` |

## About the 24h window

Every time you text a slash command, your 24h sandbox window **auto-resets**, so everyday use keeps the bot delivering to you. You only need to re-send the `join <code>` phrase if you go a full 24h without texting the bot at all.

Permanent fix (optional, later): get a Twilio-approved WhatsApp Business template (`SETUP_AUTOMATION.md §5`) — removes the 24h rule entirely.

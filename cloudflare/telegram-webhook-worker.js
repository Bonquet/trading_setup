/**
 * Telegram -> GitHub Actions relay (Cloudflare Worker).
 *
 * Makes the Telegram bot INSTANT instead of waiting for the 5-minute poll.
 * Telegram delivers each message to this Worker via webhook; the Worker fires a
 * GitHub `repository_dispatch` event that triggers .github/workflows/telegram-command.yml
 * immediately (the same pattern the WhatsApp bot used with Twilio).
 *
 * Required Worker variables/secrets (set in the Cloudflare dashboard):
 *   GITHUB_TOKEN        - GitHub PAT (fine-grained, repo trading_setup, Contents: Read/Write)
 *   GITHUB_OWNER        - Bonquet
 *   GITHUB_REPO         - trading_setup
 *   AUTHORIZED_CHAT_ID  - 5886177468  (only this chat may run commands)
 *   WEBHOOK_SECRET      - any long random string; must match the secret set on setWebhook
 *
 * See WEBHOOK_SETUP.md for the full step-by-step.
 */
export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("ok", { status: 200 });
    }

    // Verify the request really came from Telegram (secret token header).
    const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
    if (env.WEBHOOK_SECRET && got !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }

    let update;
    try {
      update = await request.json();
    } catch (e) {
      return new Response("ok", { status: 200 }); // ignore malformed
    }

    const msg = update.message || update.edited_message || {};
    const chatId = String((msg.chat && msg.chat.id) || "");
    const text = (msg.text || "").trim();

    // Only the authorized user, only slash commands.
    if (chatId !== String(env.AUTHORIZED_CHAT_ID) || !text.startsWith("/")) {
      return new Response("ok", { status: 200 });
    }

    // Fire repository_dispatch -> triggers telegram-command.yml instantly.
    const ghUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/dispatches`;
    const resp = await fetch(ghUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "telegram-webhook-worker",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        event_type: "telegram-command",
        client_payload: { text, chat_id: chatId },
      }),
    });

    // Always 200 to Telegram so it doesn't retry; log GitHub errors for debugging.
    if (!resp.ok) {
      const body = await resp.text();
      console.log(`GitHub dispatch failed ${resp.status}: ${body}`);
    }
    return new Response("ok", { status: 200 });
  },
};

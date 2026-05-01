/**
 * Twilio Function — WhatsApp inbound → GitHub Actions dispatcher
 *
 * Deploy this as a Twilio Function (Console → Functions & Assets → Services).
 * Wire it as the "Inbound URL" on your WhatsApp sandbox (or number).
 *
 * Required Environment Variables (Function service → Environment Variables):
 *   GH_OWNER       = Bonquet
 *   GH_REPO        = trading_setup
 *   GH_TOKEN       = fine-grained PAT with "Actions: write" on trading_setup
 *
 * What it does:
 *  - Parses first word of inbound message as a command (/health, /london, etc.)
 *  - POSTs a repository_dispatch to GitHub → triggers .github/workflows/whatsapp-command.yml
 *  - Replies to the user immediately with an ack via TwiML
 *  - The actual brief/health result arrives in a second outbound message when the workflow finishes (~20-40s)
 */

exports.handler = async function (context, event, callback) {
  const twiml = new Twilio.twiml.MessagingResponse();

  const raw = (event.Body || "").trim();
  const stripped = raw.replace(/^\//, "");
  const parts = stripped.split(/\s+/);
  const word = (parts[0] || "").toLowerCase();
  const args = parts.slice(1).join(" ");

  const ALLOWED = new Set([
    "health", "london", "ny", "best", "scalp", "quick", "summary",
    "accounts", "balance", "active", "risk", "took", "close", "current", "pnl",
    "buffer", "maxrisk", "style", "freeze", "unfreeze",
  ]);
  const HELP_TEXT =
    "XAU bot commands:\n" +
    "— sessions —\n" +
    "/health   check all APIs\n" +
    "/london   London brief now\n" +
    "/ny       NY brief now\n" +
    "/best     swing setup scan\n" +
    "/scalp    quick M15 scalp setup scan\n" +
    "/current  show open trades\n" +
    "/summary  weekly review\n" +
    "— accounts —\n" +
    "/accounts                  list all\n" +
    "/balance <name> <amt>      set balance\n" +
    "/active <name>             set active\n" +
    "/risk <name> <pct>         set risk %\n" +
    "— prop firm —\n" +
    "/buffer <name> <usd>       DD limit ($)\n" +
    "/maxrisk <name> <usd>      cap risk/trade ($)\n" +
    "/style <name> <s|i|s>      swing|intraday|scalp\n" +
    "/freeze <name>             block all trades on this acct\n" +
    "/unfreeze <name>           re-enable trading\n" +
    "— trade —\n" +
    "/took <acct> [lots]        mirror last trade\n" +
    "/close win|loss|be|<px> [reason]\n" +
    "/pnl                       P&L report\n" +
    "/help                      this message";

  if (!word || word === "help") {
    twiml.message(HELP_TEXT);
    return callback(null, twiml);
  }

  if (!ALLOWED.has(word)) {
    twiml.message(`Unknown command: /${word}\n\n${HELP_TEXT}`);
    return callback(null, twiml);
  }

  // Fire GitHub repository_dispatch
  const owner = context.GH_OWNER;
  const repo = context.GH_REPO;
  const token = context.GH_TOKEN;
  const url = `https://api.github.com/repos/${owner}/${repo}/dispatches`;

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "xau-bot-twilio-function",
      },
      body: JSON.stringify({
        event_type: "whatsapp-command",
        client_payload: { command: word, args: args, from: event.From || "" },
      }),
    });

    if (resp.status === 204) {
      twiml.message(`/${word} queued — result in ~30s.`);
    } else {
      const body = await resp.text();
      twiml.message(
        `/${word} failed to queue (HTTP ${resp.status}). ${body.slice(0, 140)}`
      );
    }
  } catch (err) {
    twiml.message(`/${word} dispatch error: ${String(err).slice(0, 160)}`);
  }

  return callback(null, twiml);
};

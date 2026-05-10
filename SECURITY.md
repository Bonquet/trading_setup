# Security Notes

## Rotate these keys now
The keys below were pasted into a chat conversation. Treat them as leaked. Rotate them at the first opportunity:

- **goldapi.net** — log in at https://goldapi.net/client/dashboard, regenerate key, replace `GOLDAPI_NET_KEY` in `config/.env`.
- **GoldAPI.io legacy fallback** — log in at https://www.goldapi.io, regenerate key, replace `GOLDAPI_KEY` in `config/.env` if you still use it.
- **TwelveData** — log in at https://twelvedata.com, regenerate API key, replace `TWELVEDATA_KEY` in `config/.env`.

## Rules going forward
- Never paste keys into chat, email, screenshots, or git commits.
- `config/.env` is gitignored — check `.gitignore` before committing.
- If a key is ever exposed, rotate immediately. Both providers issue new keys in seconds.
- WhatsApp tokens: same rule. Green API instance tokens and Twilio auth tokens are equally sensitive.

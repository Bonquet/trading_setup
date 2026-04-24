# Security Notes

## Rotate these keys now
Both of the keys below were pasted into a chat conversation. Treat them as leaked. Rotate them at the first opportunity:

- **GoldAPI** — log in at https://www.goldapi.io, regenerate key, replace `GOLDAPI_KEY` in `config/.env`.
- **TwelveData** — log in at https://twelvedata.com, regenerate API key, replace `TWELVEDATA_KEY` in `config/.env`.

## Rules going forward
- Never paste keys into chat, email, screenshots, or git commits.
- `config/.env` is gitignored — check `.gitignore` before committing.
- If a key is ever exposed, rotate immediately. Both providers issue new keys in seconds.
- WhatsApp tokens: same rule. Green API instance tokens and Twilio auth tokens are equally sensitive.

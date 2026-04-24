# Automation Setup — GitHub Actions + Twilio WhatsApp

This wires the bot to run **fully automatic** on GitHub's schedule and send WhatsApp signals via Twilio. No local PC needed.

## Architecture

```
GitHub Actions cron
  → checkout repo
  → python scripts/run_auto.py <session> <account>
      → fetch_gold.py       (GoldAPI + TwelveData)
      → compute_levels.py   (50 EMA, W%R, Stoch, pivots)
      → generate_signal.py  (deterministic 50 EMA Williams rules)
      → notify_whatsapp.py  (Twilio) — ONLY if Valid Trade
  → commit journal/trades.md + data/cache/*.json back to repo
```

## Schedule (`.github/workflows/trading-session.yml`)

- **07:00 UTC Mon-Fri** — London pre-open brief
- **13:00 UTC Mon-Fri** — NY pre-open brief
- **Manual** — "Run workflow" button on Actions tab (pick session + account)

GitHub cron can drift by several minutes — fine for pre-session prep.

## One-time setup steps

### 1. Push this repo to GitHub

```bash
cd "C:\Users\acebl\Documents\Trading Setup"
git init
git add .
git commit -m "initial trading setup"
# Create a private repo on github.com first, then:
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

`config/.env`, `data/cache/`, and `__pycache__/` are already gitignored.

### 2. Add GitHub repo secrets

`Settings → Secrets and variables → Actions → New repository secret` for each:

| Secret | Value |
|---|---|
| `GOLDAPI_KEY` | your GoldAPI key |
| `TWELVEDATA_KEY` | your TwelveData key |
| `TWILIO_ACCOUNT_SID` | `ACa4b729d76faf86df59a69040e2bfc6b6` |
| `TWILIO_API_KEY_SID` | starts with `SK...` (from Twilio console → API Keys & Tokens) |
| `TWILIO_API_KEY_SECRET` | the Secret shown once when the API Key was created |
| `TWILIO_FROM` | `whatsapp:+14155238886` (sandbox) or your approved WABA number |
| `TWILIO_TO` | `whatsapp:+2348126457598` |
| `TWILIO_CONTENT_SID` | *(optional — only if you have an approved 6-variable template)* |

### 3. Grant the workflow permission to push commits

`Settings → Actions → General → Workflow permissions → Read and write permissions → Save.`
Needed so the bot can append to `journal/trades.md` and commit `data/cache/signal.json`.

### 4. Twilio WhatsApp sandbox (for testing)

1. Twilio console → Messaging → Try it out → Send a WhatsApp message
2. From your phone, send the join phrase (e.g. `join stand-fresh`) to `+1 415 523 8886`
3. You're now in the 24h sandbox window — freeform messages work
4. **Every 24h of inactivity, re-send the join phrase** or messages will be silently dropped

### 5. (Later) Get an approved Business template for 24/7 signals

For always-on delivery outside the 24h window:
1. Twilio console → Content Template Builder → New template
2. Type: `text` (or `quick-reply`)
3. Body example for a 6-variable signal template:
   ```
   XAU {{1}} @ {{2}} | SL {{3}} | TP {{4}} | RR {{5}}R | {{6}}
   ```
4. Category: `MARKETING` or `UTILITY`
5. Submit for approval. Copy the `Content SID` (starts with `HX...`)
6. Paste as `TWILIO_CONTENT_SID` repo secret. `run_auto.py` will inject `{1..6}` automatically

Until approved, the workflow sends freeform messages (which need the 24h sandbox window).

## Local testing before pushing

```powershell
cd "C:\Users\acebl\Documents\Trading Setup"
# Fill TWILIO_AUTH_TOKEN in config/.env
C:\Users\acebl\AppData\Local\Programs\Python\Python312\python.exe scripts\run_auto.py local 10000
```

Expected: prints fetch → compute → signal line (or "No Trade"). If valid trade, Twilio sends to your phone and the journal gets an entry.

## Changing the schedule

Edit `.github/workflows/trading-session.yml` `cron:` lines. Cron is UTC. Examples:
- Every weekday at London + NY: current default
- Also pre-Asia scan: add `- cron: "30 23 * * 0-4"` (23:30 UTC Sun-Thu)
- Only Tue-Thu (avoid Monday gap / Friday NFP): change `1-5` to `2-4`

## Signal engine limits (important)

`generate_signal.py` implements the **50 EMA Williams** system mechanically. It **does not** attempt the Pullback strategy automatically (that one needs discretion for Fib zones + rejection candle reading). If you want Pullback signals too, open Claude in this folder and ask for a manual Pullback analysis — the playbook stays the authority.

No-trade conditions currently enforced (any one → skip):
- D1 or H4 price inside the 50 EMA channel (chop)
- D1 and H4 bias disagree
- Williams %R not firing past -20 (long) or -80 (short)
- Stochastic below 60 (long) or above 40 (short), or wrong side of its signal line
- No pivot target ≥ 2R away from entry

News filter is **not** automated — if your schedule overlaps FOMC/CPI/NFP, disable the day manually (`Actions → Disable workflow`) or add conditional logic later.

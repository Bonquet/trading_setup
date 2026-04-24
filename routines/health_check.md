# Health Check Routine

Triggered by user saying "health check", "test everything", "are you working", or "status".

## Steps

1. Run `python scripts/health_check.py` and capture the output verbatim.
2. If the user said "send test" or "test whatsapp", run `python scripts/health_check.py --send` instead (this actually fires a WhatsApp message).
3. Report back in this shape:

### Health Check — {UTC timestamp}

**Files & folders:** OK / FAIL (list any missing)
**Config (.env):** OK / FAIL
**GoldAPI:** OK (spot=$X) / FAIL (reason)
**TwelveData:** OK (last close=X) / FAIL (reason)
**Twilio auth:** OK (account status=active) / FAIL (reason)
**WhatsApp send:** (only if --send was used) OK / FAIL

**Overall:** ALL GREEN / {n} FAILURES

4. If anything failed, give the user a one-line fix suggestion per failure (e.g. "GoldAPI key may be expired — rotate at goldapi.io" or "Twilio 401 — the API Key secret in `.env` is wrong").

## Guardrails

- Don't send a WhatsApp unless the user explicitly asked to test the send.
- Don't paste secret values back in the response — only the pass/fail status and public fields (account SID, friendly_name, spot price).

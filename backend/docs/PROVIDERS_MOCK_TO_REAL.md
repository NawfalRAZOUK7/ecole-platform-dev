# Providers: mock by default, real when you're ready

Every external integration (AI, SMS, email) ships with a safe **mock/dev default**
so the platform runs end-to-end with no paid accounts and no secrets. Switching to
a real provider is a **configuration change only** — no code edits. This document
lists the exact environment variables and the selection logic.

Settings live in `app/core/config.py` (Pydantic `Settings`); every field maps to an
uppercase env var of the same name (e.g. `ai_provider` → `AI_PROVIDER`).

---

## AI (quiz generation, content helpers)

Selection happens in `app/services/ai/provider_factory.py::create_ai_provider`.

| `AI_PROVIDER` | Behaviour |
|---------------|-----------|
| `auto` (default) | Use **Claude** if `AI_API_KEY` is set; else the **open model** if `AI_OPEN_BASE_URL` is set; else the **mock**. Claude is tried first because Arabic quality matters. |
| `claude` | Paid Anthropic Claude if `AI_API_KEY` is set, else mock. |
| `open` | Free / self-hosted OpenAI-compatible endpoint if `AI_OPEN_BASE_URL` is set, else mock. |
| `mock` / unset / unknown | Deterministic free mock provider. |

Every real provider **falls back to the mock on error**, so an offline/missing
backend never breaks a request.

Enable real Claude:

```
AI_PROVIDER=auto            # or claude
AI_API_KEY=sk-ant-...       # Anthropic key
AI_MODEL=claude-sonnet-4-20250514   # optional; sensible default applied
```

Enable a free / local open model (LM Studio, Ollama-OpenAI shim, vLLM, etc.):

```
AI_PROVIDER=open            # or auto, if no Claude key is set
AI_OPEN_BASE_URL=http://localhost:1234/v1
AI_OPEN_MODEL=qwen2.5-7b-instruct
AI_OPEN_API_KEY=            # often blank for local servers
```

---

## SMS (2FA OTP)

Mock by default: `MOCK_SMS_ENABLED=true` reveals the OTP in the logs instead of
sending a real message (see `app/services/auth/sms_2fa.py` and
`app/services/communication/sms.py`).

Enable real Twilio:

```
MOCK_SMS_ENABLED=false
SMS_ENABLED=true
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
```

---

## Email (verification OTP, onboarding activation link, approvals)

Dev default points at a local SMTP catcher — `SMTP_HOST=localhost`,
`SMTP_PORT=1025` (Mailhog). Mail is captured locally, never delivered externally.
The onboarding **activation link** email rides this same path.

Enable real delivery via SMTP:

```
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...           # or mount as a secret file (SMTP_PASSWORD_FILE)
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@your-domain.ma
SMTP_FROM_NAME=École Platform
```

Or via the TestMail HTTP API (used by some test/staging setups):

```
TESTMAIL_ENABLED=true
TESTMAIL_API_KEY=...
TESTMAIL_NAMESPACE=...
```

---

## Production note

`APP_ENV=production` also tightens dev-only conveniences. For example, the
onboarding approve/resend responses only echo the raw `activation_token` (and the
email-verification OTP) **outside** production; in production the link/OTP is
delivered solely by email. Make sure real SMTP is configured before going live so
approved owners actually receive their activation link.

# Chaos Engineering — Requestly, Postman, curl, ngrok

Light chaos scenarios for validating resilience of the École Platform API
(offline-first behaviour, idempotency, rate limiting, latency tolerance).

## Scenarios

See **`backend/tests/manual/requestly-scenarios.md`** for the four canonical
scenarios:

1. Sync push 503 — offline-first validation
2. Webhook duplicate replay — PSP idempotence
3. Rate limit 429 — client retry behaviour
4. Latency 800 ms — UI loader / timeout tolerance

## Tooling

| Tool              | Purpose                                             | Install                             |
| ----------------- | --------------------------------------------------- | ----------------------------------- |
| Requestly Desktop | HTTP rule modifications (response, delay, redirect) | <https://requestly.com/desktop>     |
| Postman           | Replay collections + assertions                     | <https://www.postman.com/downloads> |
| curl              | Quick one-off requests                              | preinstalled on macOS               |
| ngrok             | Expose local API for webhooks                       | `brew install ngrok`                |

## Quick start

```bash
# 1. Start the backend
make up
# or with Doppler-injected secrets:
make doppler-run CMD="make up"

# 2. Expose for webhook testing (in another terminal)
make ngrok-webhook
#   → prints https://<random>.ngrok-free.app  (use this in tests/manual/requestly-scenarios.md §2)

# 3. Run curl chaos scripts
cd system-tests/chaos/curl
./01_sync_push_503.sh --token <jwt> --base-url http://localhost:8000/api/v1
./02_webhook_duplicate.sh --ngrok-url <ngrok-url>
./03_rate_limit_429.sh --token <jwt> --request-count 100
./04_latency_800ms.sh --token <jwt>
./05_load_smoke.sh --rps 10 --duration 30

# Or run all at once
./run-all.sh --token <jwt> --ngrok-url <ngrok-url>
```

## Artifacts

### Requestly Rules

- `requestly-rules.json` — 4 chaos rules ready for import into Requestly Desktop
- `requestly-import.md` — Import instructions and testing guide

### Curl Scripts

- `curl/01_sync_push_503.sh` — Test offline-first behaviour when sync push returns 503
- `curl/02_webhook_duplicate.sh` — Test PSP webhook deduplication
- `curl/03_rate_limit_429.sh` — Test client retry behaviour under rate limiting
- `curl/04_latency_800ms.sh` — Test UI loader/timeout tolerance with delayed sync
- `curl/05_load_smoke.sh` — Mini load test (10 RPS for 30s)
- `curl/run-all.sh` — Orchestrator to run all scripts in sequence

## Reference

- `backend/tests/manual/requestly-scenarios.md` — full scenario specs with curl
  - Postman + Requestly snippets.
- `Makefile` targets `ngrok-webhook` and `doppler-run` were added to make this
  workflow scriptable.

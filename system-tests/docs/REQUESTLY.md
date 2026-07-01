# Requestly Rules Import

Import the chaos engineering rules into Requestly Desktop to simulate failure scenarios.

## Import Steps

1. Open **Requestly Desktop** (download from https://requestly.com/desktop)
2. Go to **HTTP Rules** tab
3. Click **Import** (or drag-and-drop the JSON file)
4. Select `system-tests/chaos/requestly-rules.json`
5. Review the 7 imported rules:
   - **Chaos: Sync Push 503** — returns 503 on `/api/v1/sync/push`
   - **Chaos: Sync API Delay 800ms** — adds 800ms latency to `/api/v1/sync/*`
   - **Chaos: Rate Limit 429** — returns 429 on `/api/v1/`
   - **Chaos: Webhook Dedup Bypass** — adds `X-Bypass-Dedup: true` header to webhooks
   - **Chaos: Database Failure 503** — returns 503 on DB-dependent endpoints
   - **Chaos: Redis Failure 503** — returns 503 on cache/session endpoints
   - **Chaos: Slow Query Delay 5s** — adds 5s delay to simulate slow DB queries
6. Enable the rules you want to test (toggle on/off)

## Testing with the Rules

### Sync Push 503 (offline-first validation)

1. Enable "Chaos: Sync Push 503"
2. In the web app, trigger a sync push (e.g., submit a form)
3. Verify the app shows an offline indicator / retries locally
4. Disable the rule, sync should resume

### Sync API Delay 800ms (UI loader tolerance)

1. Enable "Chaos: Sync API Delay 800ms"
2. Trigger a sync pull in the app
3. Verify the UI shows a loader for at least 800ms
4. Verify no timeout error occurs

### Rate Limit 429 (client retry behaviour)

1. Enable "Chaos: Rate Limit 429"
2. Fire multiple rapid requests (e.g., refresh the page 10 times)
3. Verify the client shows a "rate limited" message
4. Verify retry-after logic is respected

### Webhook Dedup Bypass (idempotency)

1. Enable "Chaos: Webhook Dedup Bypass"
2. Send the same webhook twice (same `provider_event_id`)
3. Verify the second request is NOT marked as `already_processed`
4. Disable the rule and verify normal dedup behaviour returns

### Database Failure 503 (graceful degradation)

1. Enable "Chaos: Database Failure 503"
2. Navigate to a page that loads students/teachers/classes
3. Verify the app shows an error message or fallback UI
4. Verify no crash or infinite loading state

### Redis Failure 503 (cache fallback)

1. Enable "Chaos: Redis Failure 503"
2. Navigate to sessions page or perform session-dependent action
3. Verify the app falls back to DB or shows appropriate error
4. Verify session management still works (if fallback implemented)

### Slow Query Delay 5s (timeout handling)

1. Enable "Chaos: Slow Query Delay 5s"
2. Navigate to a page that loads students/teachers/classes
3. Verify the UI shows a loader for at least 5s
4. Verify no timeout error occurs (or timeout is handled gracefully)

## See Also

- `backend/tests/manual/requestly-scenarios.md` — detailed scenario specs with curl + Postman snippets
- `system-tests/chaos/curl/` — standalone curl scripts for the same scenarios
- `system-tests/postman/scenario_chaos.postman_collection.json` — Postman collection with assertions

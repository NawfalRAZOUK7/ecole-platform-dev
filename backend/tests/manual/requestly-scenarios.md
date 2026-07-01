# Chaos Engineering Scenarios — Requestly, Postman, curl, ngrok

**Reference:** `STUDENT_PACK_ROADMAP.md` §2.5 — Intercepter les requêtes HTTP  
**Tools used:** Requestly Desktop, Postman, curl, ngrok (free tier)

---

## 1. Sync push échec — 503 sur `/api/v1/sync/push`

**Objectif :** Valider le comportement offline-first quand le serveur retourne une erreur 503.

### Requestly Desktop — Rule: 503 Sync Push

1. Ouvrir Requestly Desktop → **HTTP Rules** → **New Rule** → **Modify Response**.
2. **Source condition** : `URL contains` → `/api/v1/sync/push`
3. **Response** :
   - Status Code: `503`
   - Body:

     ```json
     { "error": "Service Unavailable", "retry_after": 30 }
     ```

4. **Delay** : `30000` ms (30 s)
5. Activer la règle et tester depuis l'app web.

### curl (manuel)

```bash
# Simuler un push sync qui échoue
curl -X POST http://localhost:8000/api/v1/sync/push \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"changes": [...]}' \
  --resolve localhost:8000:127.0.0.1 \
  -w "\nHTTP %{http_code}\n"
```

---

## 2. Webhook duplicate — Déduplication PSP

**Objectif :** Vérifier que le backend rejette un webhook dupliqué (même `provider_event_id`).

> ⚠️ Les webhooks PSP arrivent de l'extérieur. Requestly ne les voit pas directement.  
> On utilise **ngrok** pour exposer l'API locale, puis **curl/Postman** pour rejouer.

### ngrok (exposer l'API locale)

```bash
# Terminal 1 — lancer ngrok (gratuit, URL temporaire)
ngrok http http://localhost:8000

# Récupérer l'URL publique, ex: https://abc123.ngrok-free.app
```

### Premier webhook (original)

```bash
curl -X POST https://abc123.ngrok-free.app/api/v1/payments/webhook/provider \
  -H "Content-Type: application/json" \
  -d '{
    "provider_event_id": "evt_424242",
    "status": "completed",
    "amount": 150.00,
    "currency": "MAD"
  }'
# → 200 OK (traité)
```

### Webhook duplicate (même `provider_event_id`)

```bash
curl -X POST https://abc123.ngrok-free.app/api/v1/payments/webhook/provider \
  -H "Content-Type: application/json" \
  -d '{
    "provider_event_id": "evt_424242",
    "status": "completed",
    "amount": 150.00,
    "currency": "MAD"
  }'
# → Doit retourner 200 OK avec "already processed" (idempotence)
```

### Postman (collection)

Créer une collection **"Webhook PSP Tests"** avec :

- **Request 1** : `POST {{ngrok_url}}/api/v1/payments/webhook/provider` → sauvegarder la réponse.
- **Request 2** : Identique → vérifier que la réponse contient `already_processed: true`.
- Ajouter un **Test script** :

  ```javascript
  pm.test("Webhook dupliqué idempotent", function () {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData.data.already_processed).to.be.true;
  });
  ```

---

## 3. Rate limit — Forcer 429 sur 1 % des requêtes

**Objectif :** Tester le comportement client quand le rate limiter backend retourne 429.

### Requestly Desktop — Rule: 429 Rate Limit

1. **New Rule** → **Modify Response**.
2. **Source condition** : `URL contains` → `/api/v1/`
3. **Response** :
   - Status Code: `429`
   - Headers:

     ```text
     Retry-After: 5
     X-RateLimit-Limit: 100
     X-RateLimit-Remaining: 0
     ```

   - Body:

     ```json
     { "error": "Too Many Requests", "retry_after": 5 }
     ```

4. **Probability** : `1 %` (si Requestly Desktop le supporte, sinon activer/désactiver manuellement)

### curl (script rapide)

```bash
#!/bin/bash
# Envoyer 100 requêtes et observer le rate limiting
for i in {1..100}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/auth/me &
  sleep 0.01
done | sort | uniq -c
```

---

## 4. Latence — 800 ms sur `/api/v1/sync/*`

**Objectif :** Simuler un réseau lent pour tester les timeouts et loaders de l'app mobile/web.

### Requestly Desktop — Rule: 800ms Latency

1. **New Rule** → **Delay Request**.
2. **Source condition** : `URL matches regex` → `.*\/api\/v1\/sync\/.*`
3. **Delay** : `800` ms
4. Activer la règle.

### curl (avec `time_total`)

```bash
# Mesurer le temps de réponse avec latence simulée
curl -w "\nTime: %{time_total}s\n" \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sync/pull
# Time: 0.850s (attendu ~800ms + overhead)
```

### Postman — Latence Sync

- Collection → **Pre-request Script** : `pm.sendRequest` avec `setTimeout` non applicable.

- Alternative : Utiliser **Postman Interceptor** + Requestly Desktop pour injecter le delay.

---

## Résumé pour le rapport (Ch.VII)

> \*« Chaos engineering légers validés via Requestly Desktop, Postman, curl et ngrok :
>
> - Simulation 503 sur sync push (offline-first)
> - Replay webhook PSP pour idempotence
> - Rate limit 429 sur 1 % des requêtes
> - Latence artificielle 800 ms sur endpoints sync »\*

---

## Prérequis

| Outil             | Installation                                         |
| ----------------- | ---------------------------------------------------- |
| Requestly Desktop | <https://requestly.com/desktop>                      |
| Postman           | <https://www.postman.com/downloads>                  |
| ngrok             | `brew install ngrok` ou <https://ngrok.com/download> |
| curl              | Préinstallé sur macOS                                |

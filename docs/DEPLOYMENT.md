# 🚀 Déploiement

## Environnements

| Env            | Fichier Compose                       | Description                         |
| -------------- | ------------------------------------- | ----------------------------------- |
| **Dev**        | `infra/docker-compose.dev.yml`        | Hot reload, logs debug, DB locale   |
| **Staging**    | `infra/docker-compose.staging.yml`    | Répliques, SSL, proche de la prod   |
| **Prod**       | `infra/docker-compose.prod.yml`       | HA, backups, Docker Secrets         |
| **Monitoring** | `infra/docker-compose.monitoring.yml` | Prometheus + Grafana + Loki + Tempo |

---

## Développement local

```bash
# Démarrer tous les services
make up

# Vérifier l'état
make health
make status

# Logs
make logs

# Arrêter
make down

# Nettoyage complet (volumes inclus)
make clean
```

### Services démarrés

| Service    | Port     | Description                   |
| ---------- | -------- | ----------------------------- |
| API        | `8000`   | FastAPI backend               |
| Web        | `5173`   | Vite dev server (npm run dev) |
| PostgreSQL | `5432`   | Base de données               |
| Redis      | `6379`   | Cache / sessions / queue      |
| Nginx      | `80/443` | Reverse proxy                 |

---

## Docker Compose — Staging

```bash
make staging-up     # Démarrer
make staging-down   # Arrêter
```

Différences avec dev :

- Images built (pas de volumes mount)
- SSL via Let's Encrypt ou certificats locaux
- Répliques API (configurable)
- Logs structurés (JSON)

---

## Kubernetes — Production

### Helm Chart

```
infra/k8s/
├── Chart.yaml              # Metadata du chart
├── values.yaml             # Valeurs par défaut
├── values-staging.yaml     # Override staging
├── values-prod.yaml        # Override production
└── templates/
    ├── deployment.yaml     # API + Worker pods
    ├── service.yaml        # ClusterIP service
    ├── ingress.yaml        # Ingress + TLS
    ├── hpa.yaml            # Horizontal Pod Autoscaler
    ├── configmap.yaml      # Configuration non-sensible
    ├── secret.yaml         # Secrets chiffrés
    ├── pvc.yaml            # Persistent Volume Claims
    ├── networkpolicy.yaml  # Règles réseau (zero-trust)
    ├── serviceaccount.yaml # Service Account avec RBAC
    ├── pdb.yaml            # Pod Disruption Budget
    ├── cronjob-backup.yaml # Backup DB automatique
    ├── job-migrate.yaml    # Job de migration (pre-deploy)
    ├── _helpers.tpl        # Templates utilitaires
    └── NOTES.txt           # Instructions post-install
```

### Déploiement

```bash
# Installation initiale
helm install ecole-platform infra/k8s/ -f infra/k8s/values-prod.yaml

# Mise à jour
helm upgrade ecole-platform infra/k8s/ -f infra/k8s/values-prod.yaml

# Rollback
helm rollback ecole-platform 1

# Statut
helm status ecole-platform
```

### Auto-scaling

Le HPA scale automatiquement entre 2 et 10 pods selon la charge CPU/mémoire :

```yaml
# values-prod.yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPU: 70
  targetMemory: 80
```

---

## CI/CD (GitHub Actions)

### Workflows

| Workflow       | Fichier                    | Déclencheur    | Actions                                          |
| -------------- | -------------------------- | -------------- | ------------------------------------------------ |
| Backend CI     | `ci.yml`                   | Push/PR → main | Lint (Ruff + MyPy), Tests (Pytest), Build Docker |
| Web CI         | `web-ci.yml`               | Push/PR → main | Lint (ESLint), Tests (Vitest), Build Vite        |
| Web E2E        | `web-e2e.yml`              | PR → main      | Tests Playwright end-to-end                      |
| Deploy Staging | `deploy-staging.yml`       | Merge → main   | Build + Push image + Deploy staging auto         |
| Deploy K8s     | `deploy-k8s.yml`           | Tag release    | Deploy production (blue-green)                   |
| Docs           | `docs.yml`                 | Push docs/     | Génération documentation API                     |
| Cleanup        | `cleanup-images.yml`       | Cron hebdo     | Nettoyage images Docker anciennes                |
| Dependabot     | `dependabot-automerge.yml` | PR Dependabot  | Auto-merge patches sécurité                      |

### Pipeline de déploiement

```
Push → main ──→ CI (lint + test + build) ──→ Deploy Staging ──→ Smoke tests
                                                                     │
Tag release ──→ CI ──→ Build prod image ──→ Push registry ──→ Deploy K8s (blue-green)
                                                                     │
                                                              Health check ──→ ✅ Switch traffic
                                                                     │
                                                              ❌ Fail ──→ Auto rollback
```

---

## Monitoring

### Démarrer le stack

```bash
make monitoring-up
```

### Accès

| Service      | URL                     | Credentials   |
| ------------ | ----------------------- | ------------- |
| Grafana      | `http://localhost:3000` | admin / admin |
| Prometheus   | `http://localhost:9090` | —             |
| Alertmanager | `http://localhost:9093` | —             |

### 8 Dashboards Grafana

1. **API Overview** — Latence, throughput, taux d'erreur, endpoints lents
2. **Database Performance** — Requêtes lentes, connexions actives, cache hit ratio
3. **Redis Metrics** — Hit rate, mémoire utilisée, commandes/sec
4. **Authentication** — Connexions, échecs, activations 2FA
5. **Business Metrics** — Inscriptions, activité élèves, contenus créés
6. **Infrastructure** — CPU, RAM, disque, réseau
7. **Logs Explorer** — Recherche dans les logs via Loki
8. **Alerting Overview** — État des alertes actives

---

## Variables d'environnement

Copier `.env.example` et configurer :

| Variable                      | Défaut                     | Description                                     |
| ----------------------------- | -------------------------- | ----------------------------------------------- |
| `APP_ENV`                     | `development`              | Environnement (development/staging/production)  |
| `DATABASE_URL`                | `postgresql+asyncpg://...` | Connexion PostgreSQL                            |
| `REDIS_URL`                   | `redis://...`              | Connexion Redis                                 |
| `JWT_SECRET_KEY`              | `change-me-...`            | Clé secrète JWT (générer une vraie clé en prod) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                       | Durée de vie access token                       |
| `MAX_SESSIONS_PER_USER`       | `5`                        | Sessions simultanées max                        |
| `LOG_LEVEL`                   | `DEBUG`                    | Niveau de log                                   |

### Secrets en production

En production, utiliser Docker Secrets ou Kubernetes Secrets :

```bash
# Docker Secrets
echo "my-secret-key" | docker secret create jwt_secret -

# Kubernetes Secrets
kubectl create secret generic ecole-secrets \
  --from-literal=jwt-secret-key=my-secret-key \
  --from-literal=db-password=my-db-password
```

---

## Object Storage (MinIO) — Phase 5 Activation

The default storage backend is **local filesystem** (`STORAGE_BACKEND=local`).
MinIO is present in dev compose but the backend does not write to it until the switch is flipped.

### Current status per environment

| Environment | `STORAGE_BACKEND` default | MinIO service                         | Ready to flip?                 |
| ----------- | ------------------------- | ------------------------------------- | ------------------------------ |
| dev         | `local`                   | ✅ running (`docker-compose.dev.yml`) | After migration script passes  |
| staging     | `local`                   | External managed MinIO / S3           | After dev is stable ≥ 24 h     |
| prod        | `local`                   | External managed MinIO / S3           | After staging is stable ≥ 24 h |

### Activation (per environment)

1. Run the migration script — must complete with `"failed": 0` and `"sample_passed": true`:

   ```bash
   python scripts/migrate_local_to_minio.py \
       --source uploads/ \
       --bucket ecole-<env>-private \
       --verify-sample 50
   ```

2. Set both variables in your environment's `.env` or secrets manager:

   ```bash
   STORAGE_BACKEND=s3
   DOCUMENT_STORAGE_BACKEND=s3
   ```

3. Restart backend and worker:

   ```bash
   # dev / staging
   docker compose -f infra/docker-compose.<env>.yml restart backend worker

   # prod (rolling)
   docker compose -f infra/docker-compose.prod.yml up -d --no-deps backend worker
   ```

4. Run the full smoke test checklist: **docs/MINIO_ROLLOUT.md §7**.

### Rollback (under 2 minutes)

```bash
# 1. Revert env vars
STORAGE_BACKEND=local
DOCUMENT_STORAGE_BACKEND=local

# 2. Restart
docker compose -f infra/docker-compose.<env>.yml restart backend worker

# 3. Verify
make health
```

Local files remain intact — the `upload_data` / `staging_uploads` / `backend_uploads` volumes
are **never removed** during the 30-day grace period after a successful flip.

For the complete rollout procedure, per-environment steps, rollback troubleshooting, and
the deferred volume cleanup instructions see **docs/MINIO_ROLLOUT.md**.

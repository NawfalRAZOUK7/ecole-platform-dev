# Doppler — Secrets Centralisés

Ce document décrit l'intégration de [Doppler](https://www.doppler.com) pour la gestion centralisée des secrets dans École Platform.

## Pourquoi Doppler ?

- Source de vérité unique pour tous les secrets (dev / staging / prod)
- Pas de `.env` committé dans le repo
- Rotation centralisée et audit log
- Injection automatique dans Docker Compose, Kubernetes et GitHub Actions

## Installation CLI

```bash
brew install dopplerhq/cli/doppler
doppler login
```

## Configuration du projet

```bash
cd ecole-platform-dev
doppler setup --project ecole-platform --config dev
```

## Importer les secrets existants

```bash
# Dev
doppler secrets upload .env --silent

# Staging (plus tard)
doppler secrets upload .env.staging --config stg_main --silent

# Production (plus tard)
doppler secrets upload .env.prod --config prd_main --silent
```

## Utilisation locale — Docker Compose

Au lieu de charger `.env` manuellement, Doppler injecte les variables au runtime :

```bash
# Dev
doppler run -- docker compose -f infra/docker-compose.dev.yml up -d

# Ou via Makefile
doppler run -- make up-doppler

# Monitoring
doppler run -- make monitoring-up
```

**Note :** Les services Docker Compose utilisent `${VAR:-default}` qui lit automatiquement les variables d'environnement du processus parent.

## Utilisation locale — Kubernetes (Kind)

```bash
# Créer les secrets dans le cluster depuis Doppler
./infra/k8s/create-secrets-from-doppler.sh ecole-local

# Déployer
./infra/k8s/deploy-local.sh
```

## Utilisation CI/CD — Kubernetes (Staging / Production)

Le workflow `.github/workflows/deploy-k8s.yml` télécharge automatiquement les secrets Doppler avant le déploiement Helm :

```yaml
- name: Sync Doppler secrets to Kubernetes
  run: |
    doppler secrets download --no-file --format docker | \
      kubectl create secret generic ecole-secrets \
        --from-env-file=/dev/stdin \
        -n ecole
```

Les pods référencent ces secrets via `envFrom.secretRef`.

## Structure des configs Doppler

| Config     | Environnement | Usage                  |
| ---------- | ------------- | ---------------------- |
| `dev`      | Development   | Local + Docker Compose |
| `stg_main` | Staging       | K8s staging            |
| `prd_main` | Production    | K8s production         |

## Secrets spécifiques par outil Student Pack

### Testmail (E2E email testing)

Ajoutez ces variables à Doppler après avoir créé votre compte Testmail via le GitHub Student Pack. La clé API est récupérée depuis <https://testmail.app/console> et n'est **pas** committée dans le repo :

```bash
doppler secrets set TESTMAIL_API_KEY "<your-testmail-api-key>" --config dev
doppler secrets set TESTMAIL_NAMESPACE "ibatt" --config dev
```

Vérifiez qu'elles sont bien injectées :

```bash
doppler secrets get TESTMAIL_API_KEY --config dev
```

Les tests E2E email utilisent ces credentials pour vérifier l'envoi réel des emails :

```bash
cd backend
pytest tests/integration/test_email_e2e.py -v
```

## Commandes utiles

```bash
# Lister les secrets
doppler secrets --config dev

# Modifier un secret
doppler secrets set DATABASE_URL "postgresql://..." --config dev

# Télécharger au format env (sans fichier)
doppler secrets download --no-file --format env

# Télécharger au format docker (pour K8s)
doppler secrets download --no-file --format docker
```

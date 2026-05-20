# 📖 Documentation — École Platform

**Démarrage rapide** — Lire dans cet ordre : [Architecture](ARCHITECTURE.md) → [Base de données](../backend/docs/DATABASE.md) (autorité Alembic vs `init.sql`) → [Tests](TESTING.md) → [Déploiement](DEPLOYMENT.md). OpenAPI : spec exportée / servie par le backend (`/openapi.json`) ; le fichier [`openapi.yaml`](openapi.yaml) sert de **référence** — régénérer depuis l’API lors des grosses évolutions pour limiter la dérive.

## Documentation technique

| Document                                                  | Description                                                                           |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [**ARCHITECTURE.md**](ARCHITECTURE.md)                    | Architecture globale, couches backend/web/mobile, patterns, diagrammes                |
| [**API-REFERENCE.md**](../backend/docs/API-REFERENCE.md)  | Référence complète des endpoints API, authentification, pagination, format de réponse |
| [**DATABASE.md**](../backend/docs/DATABASE.md)            | Schéma de base de données, groupes de migration, modèles, commandes Alembic           |
| [**DEPLOYMENT.md**](DEPLOYMENT.md)                        | Docker, Kubernetes (Helm), CI/CD, monitoring, variables d'environnement               |
| [**TESTING.md**](TESTING.md)                              | Stratégie de tests, infrastructure Pytest/Vitest/MSW, couverture par fonctionnalité   |
| [**SECURITY.md**](SECURITY.md)                            | Authentification JWT + 2FA, RBAC, protection API, audit trail, GDPR                   |
| [**CROSS-PLATFORM.md**](../mobile/docs/CROSS-PLATFORM.md) | Stratégie mobile-first/web-first, PlatformBridgeCard, cas d'utilisation               |

## Documentation par couche

| Document                                            | Description                                               |
| --------------------------------------------------- | --------------------------------------------------------- |
| [**backend/README.md**](../backend/README.md)       | Architecture backend, API endpoints, migrations, sécurité |
| [**web/README.md**](../web/README.md)               | Architecture frontend React, composants, i18n             |
| [**mobile/README.md**](../mobile/README.md)         | Architecture Flutter, Clean Architecture, Riverpod        |
| [**infra/docs/README.md**](../infra/docs/README.md) | Infrastructure Docker, Kubernetes, monitoring             |

## Référence API

| Ressource               | Lien                         |
| ----------------------- | ---------------------------- |
| Swagger UI (interactif) | http://localhost:8000/docs   |
| ReDoc                   | http://localhost:8000/redoc  |
| OpenAPI spec            | [openapi.yaml](openapi.yaml) |

## Autres documents

| Document                                                                             | Description                                         |
| ------------------------------------------------------------------------------------ | --------------------------------------------------- |
| [INNOVATION_ROADMAP.md](archive/INNOVATION_ROADMAP.md)                               | Feuille de route d'innovation produit (archivé)     |
| [KUBERNETES_SETUP.md](../infra/docs/KUBERNETES_SETUP.md)                             | Guide de déploiement Kubernetes local (Kind)        |
| [MINIO_ROLLOUT.md](../infra/docs/MINIO_ROLLOUT.md)                                   | Runbook de déploiement MinIO / stockage S3          |
| [MINIO_INTEGRATION_ARCHITECTURE.md](../infra/docs/MINIO_INTEGRATION_ARCHITECTURE.md) | Architecture de stockage S3-compatible (design doc) |
| [PAYMENT_DOCUMENTATION.md](PAYMENT_DOCUMENTATION.md)                                 | Système de facturation et paiements (implémenté)    |
| [CLAMAV.md](../infra/docs/CLAMAV.md)                                                 | Configuration antivirus ClamAV                      |

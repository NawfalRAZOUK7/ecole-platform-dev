# 📖 Documentation — École Platform

## Documentation technique

| Document | Description |
|----------|-------------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | Architecture globale, couches backend/web/mobile, patterns, diagrammes |
| [**API-REFERENCE.md**](API-REFERENCE.md) | Référence complète des endpoints API, authentification, pagination, format de réponse |
| [**DATABASE.md**](DATABASE.md) | Schéma de base de données, groupes de migration, modèles, commandes Alembic |
| [**DEPLOYMENT.md**](DEPLOYMENT.md) | Docker, Kubernetes (Helm), CI/CD, monitoring, variables d'environnement |
| [**TESTING.md**](TESTING.md) | Stratégie de tests, infrastructure Pytest/Vitest/MSW, couverture par fonctionnalité |
| [**SECURITY.md**](SECURITY.md) | Authentification JWT + 2FA, RBAC, protection API, audit trail, GDPR |
| [**CROSS-PLATFORM.md**](CROSS-PLATFORM.md) | Stratégie mobile-first/web-first, PlatformBridgeCard, cas d'utilisation |

## Documentation par couche

| Document | Description |
|----------|-------------|
| [**backend/README.md**](../backend/README.md) | Architecture backend, API endpoints, migrations, sécurité |
| [**web/README.md**](../web/README.md) | Architecture frontend React, composants, i18n |
| [**mobile/README.md**](../mobile/README.md) | Architecture Flutter, Clean Architecture, Riverpod |
| [**infra/README.md**](../infra/README.md) | Infrastructure Docker, Kubernetes, monitoring |

## Référence API

| Ressource | Lien |
|-----------|------|
| Swagger UI (interactif) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI spec | [openapi.yaml](openapi.yaml) |

## Autres documents

| Document | Description |
|----------|-------------|
| [INNOVATION_ROADMAP.md](INNOVATION_ROADMAP.md) | Feuille de route d'innovation produit |
| [clamav-setup.md](clamav-setup.md) | Configuration antivirus ClamAV |

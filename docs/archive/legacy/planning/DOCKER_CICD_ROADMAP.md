# Docker / CI-CD Roadmap

Date: 2026-03-27

## Goal

Implement the infrastructure improvements in a Docker-first order, starting with the fully free/local path.

## Recommended Order

### Phase 1 — Free / Local First

1. Add Dockerfiles for `backend` and `web`
2. Add `docker-compose.yml` for:
   - `postgres`
   - `redis`
   - `mailpit`
   - `backend`
   - `web`
3. Add `.env.example` and container-friendly local env defaults
4. Make local development work end-to-end through Docker
5. Optionally add a self-hosted GitHub Actions runner

### Phase 2 — Still Low Cost

1. Build images in CI
2. Push images to a registry
3. Prefer `GHCR` first
4. Deploy to a single Linux VPS with Docker Compose
5. Add reverse proxy and TLS with `Caddy` or `Traefik`

### Phase 3 — Paid Only When Needed

1. Managed PostgreSQL
2. Managed Redis
3. Object storage for uploads
4. Separate staging and production environments
5. Secret manager / vault integration

## Free vs Paid

### Free or local-first options

- Docker Compose
- PostgreSQL container
- Redis container
- Mailpit / MailHog
- Nginx / Caddy / Traefik
- GHCR for public or suitable GitHub-based image distribution
- GitHub Actions on public repos or self-hosted runners
- Let's Encrypt TLS
- Local filesystem uploads

### Usually paid or quota-limited

- Docker Desktop in some commercial cases
- Docker Hub private-heavy usage / higher limits
- Managed PostgreSQL
- Managed Redis
- Cloud object storage
- Cloud app hosting / Kubernetes
- Domain names
- Production SMTP/email providers

## Best Default Stack

If the objective is to respect cost first:

- local dev: Docker Compose
- CI images: GitHub Actions
- image registry: GHCR
- deployment: one Linux VPS with Docker Compose
- database first: local/containerized Postgres
- cache first: local/containerized Redis
- email dev: Mailpit
- uploads first: local disk volume

## What I Will Need From You Later

- repo visibility: public or private
- registry choice: GHCR or Docker Hub
- deployment target: local only, VPS, or cloud
- whether you want Docker Desktop compatibility only, or Linux/Podman-friendly setup
- env values or placeholders for:
  - `DATABASE_URL`
  - `REDIS_URL`
  - `JWT_SECRET_KEY`
  - `CORS_ORIGINS`
  - `SMTP_*`
  - upload path / storage choice
- whether uploads stay on local disk first
- whether Postgres and Redis should remain local containers for Phase 1

## Recommended Next Concrete Step

Start with Phase 1 only:

1. backend Dockerfile
2. web Dockerfile
3. `docker-compose.yml`
4. `.env.example`
5. local run instructions

That gives a complete free/local environment before any paid infrastructure decision.

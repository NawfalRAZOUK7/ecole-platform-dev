# École Platform

Comprehensive EdTech SaaS platform for K-12 schools in Morocco. Provides academic management (ERP), learning management (LMS), communication, billing, and AI-assisted pedagogy through a unified web and mobile experience.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.12+) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Web Frontend | React 18 + TypeScript (Vite) |
| Mobile App | Flutter |
| Infrastructure | Docker Compose, Nginx |

## Project Structure

```
ecole-platform-dev/
├── backend/          # FastAPI backend (modular monolith)
│   ├── app/          # Application code
│   │   ├── core/     # Config, database, security
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic request/response schemas
│   │   ├── api/v1/   # API route handlers
│   │   └── services/ # Business logic layer
│   ├── alembic/      # Database migrations
│   └── tests/        # Backend tests
├── web/              # React + TypeScript frontend
├── mobile/           # Flutter mobile app
├── infra/            # Infrastructure configs
│   ├── docker-compose.dev.yml
│   ├── nginx/
│   ├── postgres/
│   └── redis/
├── .env.example      # Environment variables template
├── Makefile          # Development shortcuts
└── README.md
```

## Quick Start

1. **Clone and configure:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work for local dev)
   ```

2. **Start all services:**
   ```bash
   make up
   ```

3. **Run migrations:**
   ```bash
   make migrate
   ```

4. **Verify:**
   ```bash
   make health
   # Should return: {"status": "healthy", "version": "0.1.0"}
   ```

## Common Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow service logs |
| `make migrate` | Run database migrations |
| `make test` | Run backend tests |
| `make lint` | Check code style |
| `make shell` | Open backend shell |

## Architecture

The backend follows a **modular monolith** pattern with 6 domain modules:

- **IAM** — Identity & Access Management
- **ERP** — Academic Administration
- **LMS** — Learning Management System
- **COM** — Communication & Notifications
- **Billing** — Payments & Invoicing
- **IA** — AI Features & Audit

Each module follows the **Router → Service → Repository** layer pattern. Cross-module communication uses domain events and ports/adapters.

## Documentation

Full project documentation (9 packs, 40+ documents) is available in the `ecole-platform-report/` repository:

- **Pack A** — Market & Product Vision
- **Pack B** — Product Specifications
- **Pack C** — System Design (Data Model, API Contract, RBAC)
- **Pack D** — Architecture & Quality
- **Pack E** — Frontend & Mobile Architecture
- **Pack F** — Operations & SRE
- **Pack G** — Data, Reporting & AI
- **Pack H** — Go-to-Market

## API Documentation

Once running, access the auto-generated API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

# École Platform Backend

FastAPI-based K-12 EdTech SaaS backend for Moroccan schools. Production-grade REST API with real-time WebSocket support, supporting 10-role RBAC+ABAC security model.

## Architecture

**3-tier modular monolith pattern:**
- **Router Layer** (`api/v1/*.py`) — HTTP request handlers, input validation, OpenAPI documentation
- **Service Layer** (`services/*.py`) — Business logic, domain rules, orchestration, integrations
- **Repository Layer** (`repositories/*.py`) — Async SQLAlchemy data access, query optimization

**Cross-cutting Infrastructure:**
- Security pipeline: AuthN → Context → RBAC → ABAC → Audit → Events
- SOLID principles with dependency injection via FastAPI `Depends()`
- Event-driven patterns for async tasks, notifications, and audit logging
- Domain-driven design with value objects and structural protocols

## Directory Structure

```
backend/
├── Dockerfile              # Container image
├── pyproject.toml          # Project metadata, test config, coverage rules
├── pytest.ini              # Test runner configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Dev tooling (linters, formatters)
├── requirements-test.txt   # Testing libraries
├── alembic.ini            # Database migration config
│
├── alembic/               # Database migrations
│   └── versions/          # 35+ Alembic migration files
│
├── app/                   # Main application package
│   ├── main.py           # FastAPI app factory, middleware stack, OpenAPI tags
│   ├── seed.py           # Demo data seeding script
│   ├── api/              # API layer (REST endpoints)
│   ├── core/             # Cross-cutting infrastructure
│   ├── domain/           # Domain-driven design patterns
│   ├── data/             # Static data files
│   ├── models/           # SQLAlchemy 2.0 ORM models
│   ├── repositories/     # Data access layer (queries)
│   ├── schemas/          # Pydantic v2 request/response schemas
│   ├── services/         # Business logic layer
│   ├── scripts/          # Application scripts
│   └── templates/        # Jinja2 HTML templates
│
├── docs/                 # Backend documentation
├── scripts/              # Utility scripts (OpenAPI export, validation)
├── tests/                # Test suite (unit, integration)
└── uploads/              # File storage for courses & submissions
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, pytest markers, coverage thresholds (90%) |
| `Dockerfile` | Production container image |
| `alembic.ini` | Database migration runner config |
| `requirements*.txt` | Dependency specifications |

## Running the Backend

```bash
# Development server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.scripts.seed_demo

# Run tests
pytest tests/ -v

# Export OpenAPI spec
python scripts/export_openapi.py
```

## Educational Content & Gamification APIs

Recent backend additions cover story content, coloring workflows, rewards, and configurable mini-games.

### Rewards endpoints

- `POST /api/v1/rewards/award`
  Awards stars and XP to a student and records the reward event.
- `GET /api/v1/rewards/me`
  Returns the authenticated student's rewards profile.
- `GET /api/v1/rewards/student/{student_id}`
  Returns rewards for a specific student, with access checks for parent/teacher/admin views.
- `GET /api/v1/rewards/leaderboard/{class_id}`
  Returns the class leaderboard ordered by stars and level.

### Games endpoints

- `GET /api/v1/games/configs`
  Lists game configurations with filters such as type, difficulty, subject, target age, and active state.
- `GET /api/v1/games/configs/{game_id}`
  Returns one game configuration.
- `POST /api/v1/games/configs`
  Creates a game configuration for memory, sorting, or vocabulary game modes.
- `PUT /api/v1/games/configs/{game_id}`
  Updates a game configuration.
- `POST /api/v1/games/configs/{game_id}/complete`
  Marks a game run complete and applies reward logic for the student.

### Content item endpoints

- `GET /api/v1/content-items/{content_item_id}/pages`
  Lists ordered story or coloring page assets for the reader/viewer experience.
- `POST /api/v1/content-items/{content_item_id}/pages`
  Uploads a story page asset with `page_number`, `narration_text`, `has_activity`, and `asset_type`.
- `POST /api/v1/content-items/{content_item_id}/complete`
  Marks a content item complete and awards rewards.
- `POST /api/v1/content-items/{content_item_id}/coloring/save`
  Stores a colored page submission and awards rewards for the coloring flow.

## Migrations G41-G44

The gamification and story-content schema landed through the following Alembic revisions:

- `G41` [`a81c9e4f2b7d_g41_story_content_fields.py`](./alembic/versions/a81c9e4f2b7d_g41_story_content_fields.py)
  Adds story/coloring metadata to `content_items`: `page_count`, `letter`, `target_age_min`, `target_age_max`, and `theme_color`.
- `G42` [`6d3f2a91b4c8_g42_student_rewards.py`](./alembic/versions/6d3f2a91b4c8_g42_student_rewards.py)
  Creates `student_rewards` and `reward_events` for stars, XP, levels, streaks, and reward history.
- `G43` [`b71f4d2c8e9a_g43_game_config.py`](./alembic/versions/b71f4d2c8e9a_g43_game_config.py)
  Creates `game_configs` for reusable mini-game definitions and reward settings.
- `G44` [`d4c8f1a7e2b3_g44_story_page_fields.py`](./alembic/versions/d4c8f1a7e2b3_g44_story_page_fields.py)
  Adds `page_number`, `narration_text`, `has_activity`, and `asset_type` to `content_item_assets`.

## OpenAPI Export

The generated API spec is committed in:

- [`backend/docs/openapi.json`](./docs/openapi.json)
- [`backend/openapi.json`](./openapi.json)

Regenerate it after endpoint changes with:

```bash
python scripts/export_openapi.py
```

## Security Features

- **Authentication:** JWT + optional 2FA (TOTP)
- **Authorization:** RBAC (10 roles) + ABAC (attribute-based controls)
- **Data Protection:** Password hashing, password policies, GDPR compliance
- **API Protection:** Rate limiting, idempotency keys, CORS, CSRF
- **Audit Trail:** Immutable audit logs, domain events
- **Rate Limiting:** Per-user request quotas via Redis

## Testing

- **Unit tests:** Mocked services, fast feedback
- **Integration tests:** Real database, API contracts
- **Security tests:** RBAC/ABAC matrix validation
- **Performance tests:** Load testing and benchmarks
- Coverage requirement: 90%

```bash
pytest -m "not slow" tests/  # Quick runs
pytest -m "security" tests/   # Security matrix tests
```

## Database

- **Engine:** PostgreSQL with async SQLAlchemy 2.0
- **Migrations:** Alembic version control
- **Read Replicas:** Automatic routing for read-heavy queries
- **ORM Features:** Mapped[] columns, async sessions, lazy loading
- **Connection Pool:** Smart pooling with recycling

## Next Steps

- See `app/` for application code structure
- See `alembic/versions/` for migration history
- See `tests/` for testing patterns

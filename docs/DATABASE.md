# 🗄 Base de Données

## Vue d'ensemble

- **Moteur** : PostgreSQL 16
- **ORM** : SQLAlchemy 2.0 (mode async avec asyncpg)
- **Migrations** : Alembic (async) — 56 fichiers
- **Cache** : Redis 7 (sessions, rate limiting, queue)

---

## Schéma — Groupes de migration

Les modèles sont organisés en 6 groupes principaux, migrés dans l'ordre :

### G1 — IAM (Identity & Access Management)

```
users
├── id (UUID, PK)
├── email (unique)
├── full_name
├── hashed_password
├── role (ADM/DIR/TCH/PAR/STD)
├── is_active
├── totp_enabled
└── created_at / updated_at

sessions                    memberships
├── id                      ├── id
├── user_id (FK)            ├── user_id (FK)
├── refresh_token           ├── school_id (FK)
├── ip_address              ├── role
├── user_agent              ├── status
└── expires_at              └── created_at

invitations                 totp_secrets
├── id                      ├── id
├── email                   ├── user_id (FK)
├── role                    ├── secret (encrypted)
├── school_id (FK)          └── recovery_codes
├── token
└── expires_at
```

### G2 — ERP (Administration scolaire)

```
schools                     classes                     enrollments
├── id                      ├── id                      ├── id
├── name                    ├── code                    ├── student_id (FK)
├── code                    ├── name                    ├── class_id (FK)
├── status                  ├── school_id (FK)          ├── academic_year
├── timezone                ├── level_id (FK)           └── status
└── settings (JSON)         └── teacher_id (FK)

timetable_slots             levels                      academic_periods
├── id                      ├── id                      ├── id
├── class_id (FK)           ├── code                    ├── label
├── day_of_week             ├── name                    ├── date_start
├── start_time              ├── order                   └── date_end
├── end_time                └── school_id (FK)
└── subject
```

### G3 — LMS (Learning Management)

```
content_items               quizzes                     questions
├── id                      ├── id                      ├── id
├── title                   ├── title                   ├── quiz_id (FK)
├── type (story/coloring/   ├── type                    ├── text
│   lesson/document)        ├── time_limit              ├── type (MCQ/open/...)
├── page_count              ├── class_id (FK)           ├── options (JSON)
├── letter                  └── created_by (FK)         └── correct_answer
├── target_age_min/max
└── theme_color

quiz_attempts               assignments                 submissions
├── id                      ├── id                      ├── id
├── quiz_id (FK)            ├── title                   ├── assignment_id (FK)
├── student_id (FK)         ├── class_id (FK)           ├── student_id (FK)
├── score                   ├── due_date                ├── content
├── answers (JSON)          └── rubric_id (FK)          └── grade
└── completed_at
```

### G4 — Communication

```
threads                     messages                    notifications
├── id                      ├── id                      ├── id
├── subject                 ├── thread_id (FK)          ├── user_id (FK)
├── participants            ├── sender_id (FK)          ├── type
└── created_at              ├── body                    ├── title
                            └── sent_at                 ├── body
                                                        └── read_at

announcements               events
├── id                      ├── id
├── title                   ├── title
├── body                    ├── start_at
├── school_id (FK)          ├── end_at
├── target_roles            └── school_id (FK)
└── published_at
```

### G5 — Billing

```
invoices                    payments                    fee_structures
├── id                      ├── id                      ├── id
├── invoice_number          ├── invoice_id (FK)         ├── name
├── student_id (FK)         ├── amount                  ├── amount
├── total_amount            ├── method                  ├── school_id (FK)
├── currency (MAD)          ├── status                  └── level_id (FK)
├── status                  └── paid_at
└── due_date

budget_envelopes            transactions
├── id                      ├── id
├── name                    ├── budget_id (FK)
├── total_amount            ├── amount
├── spent_amount            ├── description
├── status                  └── created_at
└── school_id (FK)
```

### G6 — Gamification & Audit

```
student_rewards             reward_events               badges
├── id                      ├── id                      ├── id
├── student_id (FK)         ├── student_id (FK)         ├── code
├── stars                   ├── event_type              ├── title_fr/ar/en
├── xp                      ├── stars_earned            ├── criteria_type
├── level                   ├── xp_earned               ├── criteria_value
├── streak_days             ├── source_type             └── is_active
├── longest_streak          └── source_id
└── badges (array)

game_configs                audit_events                feature_toggles
├── id                      ├── id                      ├── id
├── type (memory/sort/      ├── user_id (FK)            ├── key
│   vocabulary)             ├── action                  ├── enabled
├── difficulty              ├── resource_type           ├── school_id (FK)
├── config (JSON)           ├── ip_address              └── updated_at
├── reward_stars            └── timestamp
└── reward_xp
```

---

## Migrations Alembic

### Configuration

```python
# alembic/env.py — Mode async
async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

### Commandes

```bash
# Appliquer toutes les migrations
make migrate
# ou
alembic upgrade head

# Créer une nouvelle migration
make migrate-new
# ou
alembic revision --autogenerate -m "description"

# Rollback d'une migration
make migrate-down
# ou
alembic downgrade -1

# Voir l'état
make migrate-status
# ou
alembic current
```

### Historique (56 fichiers)

Les migrations sont nommées par groupe et numérotées :
- `9f7257bc8dd1_g1_g6_initial_schema.py` — Schéma initial complet
- `a81c9e4f2b7d_g41_story_content_fields.py` — Champs contenu histoires
- `6d3f2a91b4c8_g42_student_rewards.py` — Système de récompenses
- `b71f4d2c8e9a_g43_game_config.py` — Configuration jeux
- `d4c8f1a7e2b3_g44_story_page_fields.py` — Pages d'histoires
- ... et 51 autres couvrant l'évolution complète du schéma

---

## Connexion

### Développement

```
DATABASE_URL=postgresql+asyncpg://ecole:change-me@localhost:5432/ecole_platform
REDIS_URL=redis://:change-me-dev-redis@localhost:6379/0
```

### Production

- **Replicas lecture** : `DATABASE_REPLICA_URL` pour les requêtes read-heavy
- **Connection pooling** : SQLAlchemy pool avec recycling automatique
- **Backups** : CronJob Kubernetes quotidien avec rétention configurable

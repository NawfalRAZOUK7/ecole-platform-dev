# 🗄 Base de Données

## Vue d'ensemble

- **Moteur** : PostgreSQL 16
- **ORM** : SQLAlchemy 2.0 (mode async avec asyncpg)
- **Migrations** : Alembic (async) — 65+ fichiers
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
conversations               messages                    notifications
├── id                      ├── id                      ├── id
├── type (DIRECT/GROUP)     ├── conversation_id (FK)    ├── parent_id (FK)
├── subject                 ├── sender_id (FK)          ├── category
├── created_by              ├── body                    ├── title
└── created_at              └── sent_at                 ├── body
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

### G7 — Programmes Académiques (v1.1, G49–G50)

```
programs                     program_versions             program_equivalences
├── id (UUID, PK)            ├── id                       ├── id
├── code (unique)            ├── program_id (FK)          ├── from_version_id (FK)
├── title                    ├── version_label            ├── to_version_id (FK)
├── target_level             ├── effective_from           ├── equivalence_type
├── description              ├── effective_to             ├── notes
├── is_active                ├── status                    └── created_at
└── created_at               ├── snapshot_jsonb
                             └── created_at

eligibility_rules            enrollments                  program_snapshots
├── id                       ├── id                       ├── id
├── version_id (FK)          ├── student_id (FK)          ├── enrollment_id (FK)
├── rule_type (age/level/    ├── version_id (FK)          ├── version_id (FK)
│   prereq/custom)           ├── status (pending/active/  ├── snapshot_jsonb (immutable)
├── operator                 │   completed/withdrawn)     └── created_at
├── value_jsonb              ├── enrolled_at
├── error_message            ├── exited_at
└── ordering                 └── snapshot_id (FK)
```

### G8 — Conformité Fiscale (v1.1)

Champs ajoutés aux tables existantes :

```
schools (additions)                    invoice_items (additions)
├── bank_name                          ├── tva_rate         (DECIMAL 5,2)
├── bank_iban                          ├── tva_amount       (DECIMAL 12,2)
├── bank_swift                         ├── tva_base         (DECIMAL 12,2)
├── bank_rib                           └── tva_category
├── brand_logo_url
├── brand_color
├── legal_ice          (Identifiant Commun Entreprise — Maroc)
├── legal_rc           (Registre de Commerce)
└── legal_patente

reward_badges (longest_streak addition)
└── student_rewards.longest_streak     INTEGER NOT NULL DEFAULT 0
```

### G9 — Stockage Objet (v1.1)

```
storage_objects                        upload_sessions
├── id                                 ├── id
├── key (unique, S3 path)              ├── object_id (FK, nullable)
├── bucket                             ├── client_id (FK)
├── content_type                       ├── filename_original
├── size_bytes                         ├── status (initiated/uploading/
├── checksum_sha256                    │   completed/scanning/clean/infected)
├── scan_status                        ├── parts_metadata (JSON)
├── scan_completed_at                  ├── started_at
├── owner_id (FK)                      └── completed_at
├── scope (content/invoice/...)
└── created_at
```

### Timetable v1.1

Champs ajoutés à `timetable_constraints` :

```
timetable_constraints (additions)
├── max_consecutive_classes  INTEGER (nullable)
└── academic_year_id         (FK)
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

### Historique (60+ fichiers)

Les migrations sont nommées par groupe et numérotées :
- `9f7257bc8dd1_g1_g6_initial_schema.py` — Schéma initial complet
- `a81c9e4f2b7d_g41_story_content_fields.py` — Champs contenu histoires
- `6d3f2a91b4c8_g42_student_rewards.py` — Système de récompenses
- `b71f4d2c8e9a_g43_game_config.py` — Configuration jeux
- `d4c8f1a7e2b3_g44_story_page_fields.py` — Pages d'histoires
- `…_g49_academic_programs.py` — **v1.1** : programmes, versions, équivalences, snapshots
- `…_g50_eligibility_enrollments.py` — **v1.1** : règles d'éligibilité, inscriptions
- `…_g51_invoice_tva_school_branding.py` — **v1.1** : champs TVA, banking, branding
- `…_g52_storage_objects.py` — **v1.1** : tables `storage_objects` et `upload_sessions`
- `…_g53_longest_streak.py` — **v1.1** : `student_rewards.longest_streak`
- `…_g54_timetable_constraints.py` — **v1.1** : `max_consecutive_classes`, `academic_year_id`

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

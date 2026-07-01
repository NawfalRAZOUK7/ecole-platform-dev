# 🗄 Base de Données

## Vue d'ensemble

- **Moteur** : PostgreSQL 16
- **ORM** : SQLAlchemy 2.0 (mode async avec asyncpg)
- **Migrations** : Alembic (async) — 65+ fichiers
- **Cache** : Redis 7 (sessions, rate limiting, queue)

---

## Autorité du schéma (source de vérité)

| Artefact                                                                             | Rôle                                                                                                    | À modifier quand…                                                                                                     |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Migrations Alembic** ([`backend/alembic/versions/`](../backend/alembic/versions/)) | **Seule source de vérité** pour les tables, colonnes, index, contraintes et enums applicatifs.          | Toute évolution de schéma livrée en production ou partagée entre devs.                                                |
| **`infra/postgres/init.sql`**                                                        | Rôles PostgreSQL, extensions (`uuid-ossp`, etc.), privilèges par défaut — **pas** le modèle métier.     | Changement de stratégie d’accès DB, nouveaux rôles de lecture seule, extensions.                                      |
| **ORM [`backend/app/models/`](../backend/app/models/)**                              | Définition Python alignée sur les tables ; `alembic revision --autogenerate` s’en sert comme référence. | Nouvelle entité ou colonne : mettre à jour les modèles **puis** générer / écrire la migration Alembic correspondante. |

**Environnement neuf (dev / CI)** : appliquer `init.sql` (ou image Docker équivalente) pour rôles + extensions, puis **`alembic upgrade head`** pour créer toutes les tables. Ne pas dupliquer le DDL des tables dans `init.sql` — cela divergerait d’Alembic.

---

## Schéma — Groupes de migration

Les modèles sont organisés en 9 groupes principaux + groupes spécialisés, migrés dans l'ordre de dépendance :

### G1 — IAM (Identity & Access Management)

```
users
├── id (UUID, PK)
├── email (unique par school)
├── phone
├── full_name
├── password_hash
├── status (active/inactive/suspended)
├── totp_secret, totp_enabled, totp_verified_at
├── email_verified_at, phone_verified_at, phone_otp_secret, phone_otp_enabled
└── created_at / updated_at

memberships                 sessions                    login_history
├── id                      ├── id                      ├── id
├── user_id (FK)            ├── user_id (FK)            ├── user_id (FK)
├── school_id (FK)          ├── revoke_at               ├── ip_address
├── role_code (enum)        ├── source                  ├── user_agent
├── status                  ├── user_agent              ├── device_name
└── created_at              ├── ip_address              ├── success
                            ├── device_name             ├── failure_reason
                            ├── impersonator_id (FK)    └── created_at
                            └── created_at

invitation_codes            account_recovery_requests   parent_child_links
├── id                      ├── id                      ├── id
├── issuer_user_id (FK)     ├── user_id (FK)            ├── parent_user_id (FK)
├── code_hash (unique)      ├── status                  ├── child_user_id (FK)
├── role_target             ├── attempts                ├── status
├── consumed_by (FK)        ├── lock_until              ├── linked_at
├── consumed_at             ├── expires_at              ├── linked_by (FK)
├── expires_at              └── created_at              └── created_at
└── target_student_id (FK)

student_profiles            parent_profiles             teacher_profiles
├── user_id (FK, unique)    ├── user_id (FK, unique)    ├── user_id (FK, unique)
├── student_number          ├── relationship_type       ├── employee_id
├── date_of_birth           ├── cin_number              ├── subject_specialty
├── gender                  ├── address                 ├── qualification
├── class_level             ├── profession              ├── hire_date
├── nationality             └── emergency_phone       └── reward_points
└── guardian_notes

admin_profiles              content_manager_profiles    webauthn_credentials
├── user_id (FK, unique)    ├── user_id (FK, unique)    ├── id
├── department              ├── specialization          ├── user_id (FK)
├── management_level        ├── languages_managed       ├── credential_id (unique)
└── can_approve_budgets     └── approved_subjects       ├── public_key
                                                        ├── sign_count
                                                        └── device_type

oauth_accounts            password_history            failed_login_attempts
├── id                      ├── id                      ├── id
├── user_id (FK)            ├── user_id (FK)            ├── user_id (FK)
├── provider                ├── password_hash           ├── email
├── provider_user_id        └── created_at              ├── ip_address
├── provider_email                                      ├── user_agent
└── token_expires_at                                    └── failure_reason

known_locations             known_devices
├── id                      ├── id
├── user_id (FK)            ├── user_id (FK)
├── ip_address              ├── device_fingerprint
├── country_code            ├── device_name
├── city                    ├── user_agent
└── is_suspicious           └── is_suspicious
```

### G2 — ERP (Administration scolaire)

```
schools                     academic_years              periods
├── id                      ├── id                      ├── id
├── name                    ├── label                   ├── academic_year_id (FK)
├── code (unique)           ├── date_start              ├── label
├── status                  ├── date_end                ├── status
├── timezone                └── created_at              ├── date_start
├── default_language                                    ├── date_end
├── grading_scale                                       └── created_at
├── settings (JSONB)        classes                     enrollments
├── rib, iban, bic         ├── id                      ├── id
├── bank_name               ├── code                    ├── student_id (FK)
├── tva_number              ├── academic_year_id (FK)   ├── class_id (FK)
├── tax_id                  ├── name                    ├── period_id (FK)
└── brand_color, …        └── created_at              ├── status
                                                        └── created_at

teacher_assignments         attendance_sessions         attendance_records
├── id                      ├── id                      ├── id
├── class_id (FK)           ├── class_id (FK)           ├── session_id (FK)
├── teacher_id (FK)         ├── date                    ├── student_id (FK)
├── period_id (FK)          ├── slot_label              ├── status
└── created_at              ├── created_by (FK)         ├── notes
                            └── created_at              └── created_at

absence_justifications      justification_reviews     attendance_alerts
├── id                      ├── id                      ├── id
├── student_id (FK)         ├── justification_id (FK)   ├── student_id (FK)
├── session_id (FK)         ├── reviewer_id (FK)        ├── period_id (FK)
├── reason                  ├── status                  ├── threshold_type
├── attachments (JSON)      ├── comment                 ├── threshold_value
└── created_at              └── created_at              └── triggered_at

timetable_slots             timetable_exceptions      timetable_constraints
├── id                      ├── id                      ├── id
├── class_id (FK)           ├── slot_id (FK)            ├── school_id (FK)
├── day_of_week             ├── date                    ├── constraint_type
├── start_time              ├── exception_type          ├── priority
├── end_time                ├── substitute_teacher_id   ├── data (JSONB)
├── subject                 └── created_at              └── created_at
└── created_at
timetable_generation_jobs
├── id
├── status
├── result_json
└── created_at
```

### G3 — LMS (Learning Management)

```
courses                     assignments                 submissions
├── id                      ├── id                      ├── id
├── class_id (FK)           ├── course_id (FK)          ├── assignment_id (FK)
├── teacher_id (FK)         ├── title                   ├── student_id (FK)
├── title                   ├── description             ├── content
├── description             ├── due_date                ├── status
└── status                  ├── max_score               ├── submitted_at
                            └── created_at              └── created_at

submission_files            grades                      grade_categories
├── id                      ├── id                      ├── id
├── submission_id (FK)      ├── submission_id (FK)      ├── class_id (FK)
├── filename                ├── score                   ├── period_id (FK)
├── file_path               ├── max_score               ├── name
├── size_bytes              ├── percentage              ├── weight
└── created_at              ├── graded_by (FK)          └── position
                            └── created_at

rubrics                     rubric_criteria             rubric_levels
├── id                      ├── id                      ├── id
├── teacher_id (FK)         ├── rubric_id (FK)          ├── criterion_id (FK)
├── title                   ├── title                   ├── label
├── description             ├── weight                  ├── points
├── total_points            └── position                └── position
└── is_template

rubric_scores               assessments                 assessment_results
├── id                      ├── id                      ├── id
├── rubric_id (FK)          ├── class_id (FK)           ├── assessment_id (FK)
├── criterion_id (FK)       ├── title                   ├── student_id (FK)
├── score                   ├── description             ├── score
└── created_at              ├── max_score               ├── percentage
                            ├── date                    └── created_at
                            └── created_at

content_items               content_item_assets         content_progress
├── id                      ├── id                      ├── id
├── school_id (FK, null)    ├── content_item_id (FK)    ├── student_id (FK)
├── title                   ├── filename                ├── item_id (FK)
├── type                    ├── file_path               ├── status
├── body (JSONB)            ├── mime_type               ├── progress_pct
└── status                  └── size_bytes              └── updated_at

quizzes                     quiz_questions              quiz_attempts
├── id                      ├── id                      ├── id
├── school_id (FK, null)    ├── quiz_id (FK)            ├── quiz_id (FK)
├── title                   ├── text                    ├── student_id (FK)
├── description             ├── type (MCQ/TF/FILL/      ├── attempt_no
├── time_limit_minutes      │   MATCHING)               ├── score
└── passing_score           ├── options (JSON)          ├── status
                            ├── correct_answer          └── created_at
                            └── position

quiz_responses              activities                  activity_sessions
├── id                      ├── id                      ├── id
├── attempt_id (FK)         ├── school_id (FK, null)    ├── activity_id (FK)
├── question_id (FK)        ├── title                   ├── student_id (FK)
├── answer                  ├── type                    ├── score
└── is_correct              ├── config (JSONB)          ├── status
                            └── created_at              └── created_at

question_bank_items         class_content_assignments   content_submissions
├── id                      ├── id                      ├── id
├── school_id (FK)          ├── class_id (FK)           ├── school_id (FK)
├── text                    ├── content_item_id (FK)    ├── title
├── type                    └── created_at              ├── body
├── options (JSON)                                      ├── status
└── correct_answer                                      └── created_at

student_period_averages
├── id
├── student_id (FK)
├── class_id (FK)
├── period_id (FK)
└── average
```

### G4 — Communication

```
consent_preferences         notifications               notification_preferences
├── id                      ├── id                      ├── id
├── user_id (FK)            ├── school_id (FK)          ├── user_id (FK)
├── topic                   ├── user_id (FK)            ├── channel
├── channel                 ├── category                ├── category
├── scope_type              ├── title                   ├── enabled
├── scope_ref_id            ├── body                    └── created_at
└── status                  ├── data (JSONB)
                            ├── read_at
                            └── created_at

notification_deliveries     device_tokens               parent_feed_items
├── id                      ├── id                      ├── id
├── notification_id (FK)    ├── user_id (FK)            ├── school_id (FK)
├── channel                 ├── platform                ├── parent_id (FK)
├── status                  ├── token                   ├── item_type
└── created_at              └── created_at              ├── item_data (JSON)
                                                        └── created_at

conversations               conversation_participants   messages
├── id                      ├── id                      ├── id
├── type (DIRECT/GROUP)     ├── conversation_id (FK)    ├── conversation_id (FK)
├── school_id (FK)          ├── user_id (FK)            ├── sender_id (FK)
└── created_at              ├── role                    ├── body
                            └── created_at              ├── attachments
                                                        └── created_at

message_read_receipts       announcements               shared_review_comments
├── id                      ├── id                      ├── id
├── message_id (FK)         ├── school_id (FK)          ├── school_id (FK)
├── user_id (FK)            ├── title                   ├── parent_id (FK)
└── read_at                 ├── body                    ├── student_id (FK)
                            ├── target_roles            ├── content_type
                            └── published_at            ├── comment
                                                        └── created_at
```

### G5 — Billing & Finance

```
invoices                    invoice_items               payment_attempts
├── id                      ├── id                      ├── id
├── parent_id (FK)          ├── invoice_id (FK)       ├── invoice_id (FK)
├── period_id (FK)          ├── description             ├── amount
├── status                  ├── quantity                ├── method
├── total_amount            ├── unit_price              ├── status
├── currency                ├── amount                  ├── provider_ref
├── issued_date             ├── tva_rate                └── created_at
└── due_date                └── created_at

payment_proofs              provider_webhook_events     fee_structures
├── id                      ├── id                      ├── id
├── payment_id (FK)         ├── provider                ├── school_id (FK)
├── filename                ├── event_id                ├── name
├── file_path               ├── payload (JSON)          ├── amount
└── created_at              └── created_at              ├── frequency
                                                        └── status

fee_assignments             sibling_discount_policies   late_fee_policies
├── id                      ├── id                      ├── id
├── fee_structure_id (FK)   ├── school_id (FK)          ├── school_id (FK)
├── student_id (FK)         ├── min_siblings            ├── days_overdue_threshold
├── status                  ├── discount_pct            ├── fee_amount
└── created_at              └── created_at              └── created_at

payment_plans               installments                micro_budgets
├── id                      ├── id                      ├── id
├── invoice_id (FK)         ├── plan_id (FK)            ├── school_id (FK)
├── total_amount            ├── amount                  ├── academic_year_id (FK)
├── installment_count       ├── due_date                ├── total_amount
└── created_at              ├── status                  ├── allocated_amount
                            └── created_at              ├── remaining_amount
                                                        └── status

budget_allocations          budget_requests             budget_transactions
├── id                      ├── id                      ├── id
├── budget_id (FK)          ├── budget_id (FK)          ├── allocation_id (FK)
├── class_id (FK)           ├── requester_id (FK)       ├── type
├── amount                  ├── amount                  ├── amount
└── created_at              ├── status                  └── created_at
                            └── created_at

retention_metrics           cashflow_forecasts          financial_snapshots
├── id                      ├── id                      ├── id
├── school_id (FK)          ├── school_id (FK)          ├── school_id (FK)
├── year_from               ├── month                   ├── metric_name
├── year_to                 ├── expected_income         ├── value
├── retention_rate          ├── actual_income           └── created_at
└── created_at              └── created_at
cost_per_student_metrics
├── id
├── school_id (FK)
├── academic_year_id (FK)
├── cost
└── created_at
```

### G6 — Gamification, AI & Audit

```
game_configs                reward_badges               student_rewards
├── id                      ├── id                      ├── id
├── school_id (FK, null)    ├── code (unique)           ├── student_id (FK)
├── type                    ├── title_fr/ar/en          ├── stars
├── difficulty              ├── description_fr/ar/en    ├── xp
├── config (JSONB)          ├── criteria_type           ├── level
├── reward_stars            ├── criteria_value          ├── streak_days
└── reward_xp               └── is_active               └── longest_streak

reward_events               skill_dimensions            skill_milestones
├── id                      ├── id                      ├── id
├── student_id (FK)         ├── code (unique)           ├── dimension_id (FK)
├── event_type              ├── name_fr/ar/en           ├── code
├── stars_earned            ├── description_fr          ├── name_fr/ar
└── created_at              ├── icon                    ├── level
                            └── display_order           ├── rule_config (JSON)

skill_progress              audit_logs                  feature_toggles
├── id                      ├── id                      ├── id
├── student_id (FK)         ├── school_id (FK)          ├── feature_key (unique)
├── milestone_id (FK)       ├── actor_id (FK)           ├── display_name
└── created_at              ├── action_type             ├── description
                            ├── target_type             ├── enabled_globally
                            ├── entity_before (JSONB)   ├── enabled_school_ids
                            ├── entity_after (JSONB)    └── enabled_role_codes
                            └── created_at

difficulty_adaptations      writing_attempts            ai_preferences
├── id                      ├── id                      ├── id
├── student_id (FK)         ├── student_id (FK)         ├── user_id (FK)
├── subject                 ├── subject                 ├── target_user_id (FK)
├── previous_difficulty     ├── input_text              └── opt_out
├── new_difficulty          ├── suggestion
└── reason                  └── created_at
```

### G7 — Academic Programs (v1.1+)

```
programs                    program_versions            program_assignment_events
├── id (UUID, PK)           ├── id                      ├── id
├── code (unique)           ├── program_id (FK)         ├── student_id (FK)
├── title                   ├── version_label           ├── program_id (FK)
├── target_level            ├── effective_from            ├── reason
├── description             ├── effective_to            └── created_at
├── is_active               ├── status
└── created_at              └── created_at

program_equivalences        academic_snapshots          eligibility_rules
├── id                      ├── id                      ├── id
├── from_program_id (FK)    ├── student_id (FK)         ├── program_id (FK)
├── to_program_id (FK)      ├── academic_year_id (FK)   ├── kind
├── equivalence_type        ├── kind                    ├── condition_type
└── created_at              ├── snapshot_jsonb          ├── condition_value (JSONB)
                            └── created_at              └── created_at
```

### G8 — Compliance & Reporting

```
men_curricula               men_objectives              curriculum_mappings
├── id                      ├── id                      ├── id
├── level                   ├── curriculum_id (FK)      ├── objective_id (FK)
├── grade                   ├── code                    ├── course_id (FK)
├── subject                 ├── title_fr/ar             ├── coverage_pct
├── academic_year           ├── trimester               └── created_at
└── version                 └── display_order

compliance_reports          report_schedules            report_jobs
├── id                      ├── id                      ├── id
├── curriculum_id (FK)      ├── school_id (FK)          ├── school_id (FK)
├── generated_at            ├── created_by (FK)         ├── requester_id (FK)
├── coverage_pct            ├── report_type             ├── type
└── created_at              ├── frequency               ├── parameters (JSONB)
                            ├── parameters (JSONB)      ├── status
                            └── created_at              ├── file_path
                                                        └── created_at

data_exports
├── id
├── school_id (FK)
├── requester_id (FK)
├── entity
├── format
└── row_count
```

### G9 — Stockage, Documents & Sync

```
documents                   document_versions           upload_sessions
├── id                      ├── id                      ├── id
├── school_id (FK)          ├── document_id (FK)      ├── upload_state
├── uploader_id (FK)        ├── version_number          ├── kind
├── filename                ├── filename                ├── object_key
├── original_filename       ├── file_path               ├── mime_type
├── mime_type               ├── size_bytes              ├── size_bytes
├── size_bytes              └── created_at              ├── school_id (FK)
├── sha256                                            ├── uploader_id (FK)
├── storage_path                                      ├── scope_data (JSONB)
├── category                                          ├── expires_at
└── created_at                                        └── created_at

sync_devices                sync_queue                  sync_checkpoints
├── id                      ├── id                      ├── id
├── school_id (FK)          ├── device_id (FK)          ├── device_id (FK)
├── device_name             ├── operation               ├── last_sync_at
├── device_type             ├── entity_type             └── checksum
└── last_seen_at            ├── entity_id
                            ├── status
                            └── created_at

sync_conflicts
├── id
├── queue_item_id (FK)
├── resolution
└── created_at
```

### Niveaux & Cartographie Âge (G46)

```
level_age_mappings
├── id
├── level_code
├── label_fr/ar/en
├── default_age_min
├── default_age_max
├── display_order
└── school_id (FK, null = default plateforme)
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

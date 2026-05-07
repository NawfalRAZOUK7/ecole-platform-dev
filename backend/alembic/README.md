# alembic/ — Database Migrations

Alembic database schema version control. Manages incremental schema changes with reversibility.

## Overview

Alembic tracks database schema evolution:
- **Automatic migrations** — Generated from SQLAlchemy model changes
- **Manual migrations** — Custom SQL for complex changes
- **Version control** — Git-tracked migration history
- **Upgrade/downgrade** — Forward and backward schema transitions
- **Multi-environment** — Dev, test, production configs

## Directory Structure

```
alembic/
├── env.py               # Migration environment configuration
├── script.py.mako       # Migration file template
├── versions/            # Individual migration files
│   ├── 9f7257bc8dd1_g1_g6_initial_schema_iam_erp_lms_com.py
│   ├── a2f8b3c4d5e6_g7_ai_writing_attempts_preferences.py
│   ├── b3c4d5e6f7a8_g8_parent_child_links_views_kpi.py
│   ├── ... (65+ total migrations)
│   └── b2c3d4e5f6a7_g51a_attendance_performance_indexes.py
│
└── (no other config files — see alembic.ini in backend/)
```

## Core Files

### env.py

Migration execution environment:
- Configures database connection
- Sets up logging
- Defines migration modes (upgrade/downgrade)
- Handles schema comparisons for auto-generation

Key sections:
```python
# Get database URL from config
config = context.config
sqlalchemy_url = settings.database_url

# Run migrations in offline mode (for SQL script generation)
if context.is_offline_mode():
    context.run_migrations()

# Or in online mode (actual execution)
else:
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

### script.py.mako

Jinja2 template for generating new migration files:
- Defines migration file structure
- Import statements
- `upgrade()` and `downgrade()` functions
- Comments and metadata

Generated migrations follow standard pattern:

```python
"""migration message

Revision ID: abc123def456
Revises: xyz789uvw012
Create Date: 2024-03-30 10:15:30.123456
"""

from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'xyz789uvw012'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Apply schema changes."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        # ... columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade() -> None:
    """Revert schema changes."""
    op.drop_table('users')
```

## versions/ — Migration History

65+ migrations covering:

### G1-G10: Core Schema & Foundation
- Initial tables (users, roles, permissions, schools, classes, academic_years)
- AI writing attempts and preferences
- Parent-child links and views
- Session device info and password policy
- TOTP 2FA and email verification
- GIN indexes and full-text search
- Role-specific profiles

### G11-G20: Content & Assessment
- PDF exercise workflows
- Timetable slots and exceptions
- Fee structures and billing enhancements
- Messaging and announcements
- Feature toggles
- Expanded role code columns
- Teacher reward points
- Quiz engine and assignment fields
- Content library models

### G21-G30: Notifications & Operations
- Notification center
- Reports and analytics
- Calendar events
- Document management
- OOP admin and content manager profiles
- IAM impersonation and login history
- Billing policies and payment plans
- Rubric engine
- Weighted gradebook
- Question bank items
- Late submission penalties

### G31-G40: Performance & Infrastructure
- School model mixins
- PostgreSQL enum columns
- Micro-école models
- Class micro-budgets
- Life skills passport
- MEN compliance checker
- Local-first sync
- Financial health dashboard
- Foreign key indexes (G37a, G37b)
- Grade 0-20 check constraints
- Remaining foreign key indexes

### G41-G51: Content & Uploads
- Story content fields
- Student rewards
- Game configuration
- Story page fields
- Level-age mappings
- Longest streak tracking
- Reward badges
- Timetable constraints
- Program management and history
- Program versions, equivalences, snapshots
- Eligibility rules
- Upload sessions
- Invoice PDF banking details
- Attendance performance indexes

### Merge Migrations
- G48 + I4 merge (absence justification + difficulty adaptations)

## Migration Naming Convention

```
{12-char-hex}_{group}_{description}.py

Examples:
9f7257bc8dd1_g1_g6_initial_schema_iam_erp_lms_com.py
a2f8b3c4d5e6_g7_ai_writing_attempts_preferences.py
b3c4d5e6f7a8_g8_parent_child_links_views_kpi.py
```

- **12-char hex**: First 12 characters of the Alembic revision ID
- **group**: Logical feature group (g1-g51a, h2, i4)
- **description**: Semantic description of what changed

## Working with Migrations

### Auto-generate migration

```bash
# Compare models to database schema
alembic revision --autogenerate -m "add user verification"

# Review generated migration
cat alembic/versions/abc123_add_user_verification.py

# Edit if needed (manual adjustments)
nano alembic/versions/abc123_add_user_verification.py
```

### Manual migration

```bash
# Create empty migration
alembic revision -m "custom data migration"

# Write upgrade() and downgrade() manually
nano alembic/versions/xyz789_custom_data_migration.py
```

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply to specific migration
alembic upgrade abc123def456

# Upgrade one at a time (safe)
alembic upgrade +1
```

### Revert migrations

```bash
# Downgrade one migration
alembic downgrade -1

# Downgrade to specific migration
alembic downgrade xyz789uvw012

# Downgrade all
alembic downgrade base
```

### Check migration status

```bash
# Show current schema version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic upgrade head --sql  # Dry-run
```

## Migration Best Practices

### 1. One concern per migration

Bad: 20 unrelated changes in one file
Good: One logical change (e.g., add user verification fields)

### 2. Data migrations separate from schema

Schema only:
```python
def upgrade():
    op.add_column('users', sa.Column('verified_at', sa.DateTime()))
```

Data migration:
```python
def upgrade():
    op.execute("UPDATE users SET verified_at = NOW() WHERE is_verified = true")
```

### 3. Reversible migrations

Always provide downgrade():
```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone')
```

### 4. Index migrations for performance

Add indexes in separate migrations:
```python
def upgrade():
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_users_email'), table_name='users')
```

### 5. Constraint migrations carefully

Large tables may lock during constraint adds:
```python
# Option 1: Add constraint with validation (locks table)
def upgrade():
    op.create_check_constraint(
        'ck_grade_range',
        'grades',
        'grade >= 0 AND grade <= 20'
    )

# Option 2: Deferred constraint (PostgreSQL specific)
def upgrade():
    op.execute("""
        ALTER TABLE grades
        ADD CONSTRAINT ck_grade_range
        CHECK (grade >= 0 AND grade <= 20)
        NOT VALID;
        ALTER TABLE grades VALIDATE CONSTRAINT ck_grade_range;
    """)
```

### 6. Test migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade base

# Verify data integrity
SELECT COUNT(*) FROM users;
SELECT * FROM alembic_version;
```

## Environment Configuration

Alembic settings in `../alembic.ini`:
```ini
[alembic]
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/ecole
script_location = alembic
sqlalchemy.echo = false
```

Overridden by `DATABASE_URL` environment variable for deployment.

## Integration with CI/CD

```bash
# In deployment pipeline
alembic upgrade head  # Apply pending migrations

# In development
alembic revision --autogenerate -m "description"
git add alembic/versions/
git commit -m "feat: add user verification schema"
```

## Schema Validation

After migrations, validate schema:

```bash
# Check migrations are in sync with models
alembic upgrade head
python -c "from app.models import *; print('Schema valid')"

# Test with actual data
pytest tests/integration/ -v
```

## Troubleshooting

### Migration conflicts

If multiple developers create migrations:
```bash
# Resolve merge conflicts in alembic/versions/
# Edit alembic/versions/merge_*.py
# Update down_revision to point to both parents
```

### Out of sync schema

If database is out of sync with migrations:
```bash
# Reset development database
alembic downgrade base
alembic upgrade head

# Production: careful manual intervention
# - Backup database first
# - Review migration diffs
# - Apply incrementally
```

### Slow migration

```python
# Add session with batch mode (PostgreSQL)
def upgrade():
    with op.batch_operations() as batch_op:
        batch_op.add_column('users', sa.Column('new_field', ...))
```

## Next Steps

- See `app/models/` for SQLAlchemy model definitions
- See `scripts/validate_migrations.py` for migration validation
- See `versions/TRACEABILITY.md` for full migration traceability matrix
- See Git history for migration details: `git log alembic/versions/`

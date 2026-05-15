# PostgreSQL Initialization

PostgreSQL database initialization scripts for the Ecole Platform. This directory prepares PostgreSQL roles, extensions, and permissions; application schema changes are owned by Alembic.

## Files

- **init.sql** - SQL initialization script executed on first PostgreSQL container startup

## What Gets Initialized

### Databases
- Current PostgreSQL database selected by the container environment

### Extensions
- `uuid-ossp` - UUID generation functions
- `pgcrypto` - Cryptographic functions
- `plpgsql` - Procedural language (default)

### Roles and Permissions
- Application user role (limited permissions)
- Read-only role for backups
- Replication role where needed
- Default schema privileges for tables and sequences created later by migrations

### Application Schema

Do not add application tables, indexes, constraints, enums, or views to `init.sql`. Those belong in Alembic migrations under `backend/alembic/versions/`, with the current database state reached by running `alembic upgrade head`.

## Execution

Script is automatically executed by PostgreSQL when container first starts:
```bash
docker-compose -f docker-compose.dev.yml up postgres
```

PostgreSQL mounts `init.sql` at `/docker-entrypoint-initdb.d/` and executes on startup.

## Development Database

For development, the init script creates or configures:
- Role `app_user` with application permissions (read/write)
- Role `app_readonly` with read-only access
- Role `replicator` with replication privileges
- User `postgres` (admin)

## Modifying Schema

To add new application tables or columns:

1. Create an Alembic revision in `backend/alembic/versions/`
2. Apply it with `alembic upgrade head`
3. Leave `init.sql` unchanged unless the migration needs a new database extension or role privilege

To add roles, privileges, or extensions:

1. Edit `init.sql`
2. For development: Delete PostgreSQL volume and restart:
   ```bash
   docker-compose -f docker-compose.dev.yml down -v
   docker-compose -f docker-compose.dev.yml up postgres
   ```
3. For shared environments: document the operational step in the deployment runbook

## Backup Integration

Backup user `ecole_backup` has read-only permissions for safe backups:
```bash
pg_dump -U ecole_backup -d ecole_platform > backup.sql
```

See `../backup/README.md` for backup procedures.

## Security Considerations

- Application user has limited permissions (no DDL/DCL)
- Passwords should be loaded from environment variables or secrets
- Row-level security enforced via policies (if applicable)
- Connection from app to postgres uses encrypted channel
- All queries use parameterized statements (handled by ORM)

## Connection String

For application use:
```
postgresql+asyncpg://app_user:$APP_DB_PASSWORD@postgres:5432/ecole_platform
```

Configure in environment or secrets file.

## Troubleshooting

**Schema not created on startup:**
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify init.sql syntax with `psql -f init.sql`
- Ensure database volume is clean (no prior data)

**Permission denied errors:**
- Verify user permissions in init.sql
- Check application connection user and password
- Confirm role assignments in GRANT statements

**Extension installation fails:**
- Some extensions may not be available in all PostgreSQL versions
- Adjust extensions list for your PostgreSQL version
- Check extension availability: `\dx` in psql

## Monitoring

See `../prometheus/README.md` for PostgreSQL metrics collection.
See `../grafana/dashboards/README.md` for database health dashboard.

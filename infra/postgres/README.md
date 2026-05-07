# PostgreSQL Initialization

PostgreSQL database initialization scripts for the Ecole Platform. Creates database schema, extensions, roles, and configures permissions.

## Files

- **init.sql** - SQL initialization script executed on first PostgreSQL container startup

## What Gets Initialized

### Databases
- Main application database
- Staging and testing databases (if configured)

### Extensions
- `uuid-ossp` - UUID generation functions
- `pgcrypto` - Cryptographic functions
- `plpgsql` - Procedural language (default)
- `json` and `jsonb` - JSON support (built-in for modern PostgreSQL)

### Roles and Permissions
- Application user role (limited permissions)
- Read-only role for backups
- Admin role with full privileges
- Row-level security policies (if configured)

### Schema Objects
- Tables with appropriate indexes
- Sequences for auto-incrementing IDs
- Foreign key constraints
- Check constraints for data integrity
- Views for common query patterns

## Execution

Script is automatically executed by PostgreSQL when container first starts:
```bash
docker-compose -f docker-compose.dev.yml up postgres
```

PostgreSQL mounts `init.sql` at `/docker-entrypoint-initdb.d/` and executes on startup.

## Development Database

For development, the init script creates:
- Role `app_user` with application permissions (read/write)
- Role `app_readonly` with read-only access
- Role `replicator` with replication privileges
- User `postgres` (admin)

## Modifying Schema

To add new tables or extensions:

1. Edit `init.sql` with new schema changes
2. For development: Delete PostgreSQL volume and restart:
   ```bash
   docker-compose -f docker-compose.dev.yml down -v
   docker-compose -f docker-compose.dev.yml up postgres
   ```
3. For production: Use migration tools (Alembic, Flyway) for schema changes

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
postgresql://ecole_app:$DB_PASSWORD@postgres:5432/ecole_platform
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

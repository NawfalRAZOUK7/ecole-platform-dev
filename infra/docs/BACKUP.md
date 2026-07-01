# Database Backup & Recovery

PostgreSQL backup and disaster recovery scripts for the Ecole Platform. Supports automated backups, point-in-time restore, compliance audits, and disaster recovery drills.

## Scripts

### Backup Operations

- **pg_backup.sh** - Create PostgreSQL database dump with compression
  - Exports all databases in custom format for efficient storage
  - Includes schema, data, and indexes
  - Compressed output suitable for S3 archival

### Recovery Operations

- **pg_restore.sh** - Restore database from dump file
  - Validates dump file integrity
  - Restores to running PostgreSQL instance
  - Logs restore progress and errors
  - Includes point-in-time restore support via dump timestamps

- **restore_drill.sh** - Automated disaster recovery drill
  - Simulates recovery in staging environment
  - Validates backup integrity without affecting production
  - Generates restore time estimates
  - Documents recovery success metrics

### Compliance & Audit

- **audit_worm_export.sh** - WORM (Write Once Read Many) compliance export
  - Exports audit logs and audit trail data
  - Creates immutable compliance archive
  - Supports retention policies for regulatory requirements
  - Generates checksums for integrity verification

## Quick Start

### Create Backup
```bash
./pg_backup.sh
# Creates: ecole_backup_2026-03-30_143022.sql.gz
```

### Restore from Backup
```bash
./pg_restore.sh ecole_backup_2026-03-30_143022.sql.gz
```

### Run Recovery Drill
```bash
./restore_drill.sh staging
# Tests recovery in staging environment
```

### Generate Compliance Export
```bash
./audit_worm_export.sh /path/to/archive
```

## Backup Strategy

- **Frequency** - Daily automated backups (scheduled in DEPLOYMENT.md)
- **Retention** - 30 days local, 1 year S3 archival
- **Encryption** - Backups encrypted at rest in S3
- **Verification** - Automated restore drills weekly
- **Location** - Local `/backups/` directory + S3 bucket

## Disaster Recovery

To recover from backup:

1. Stop production services
2. Run `pg_restore.sh <backup-file>`
3. Verify data integrity with queries
4. Restart application services
5. Monitor for data anomalies

See `../DEPLOYMENT.md` for detailed RTO/RPO targets and runbooks.

## Integration

Backups are uploaded to S3 via:
```bash
../scripts/backup-s3.sh ecole_backup_2026-03-30_143022.sql.gz
```

Automated daily backup cron job configured in production deployment.

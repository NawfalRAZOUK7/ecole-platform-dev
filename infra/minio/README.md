# MinIO Object Storage

MinIO is used **for local development only** as an S3-compatible object storage backend.

## Purpose

In development, MinIO provides:
- S3-compatible API for file uploads/downloads
- Local bucket storage without external cloud dependencies
- ILM (lifecycle) rules for automatic cleanup
- SSE-S3 encryption simulation

## Production & Staging

**MinIO is NOT used in production or staging.**

Production and staging environments use external S3-compatible storage:
- AWS S3
- DigitalOcean Spaces
- Any S3-compatible provider

Configure via environment variables:
```bash
STORAGE_BACKEND=s3
S3_ENDPOINT=https://s3.provider.com
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_BUCKET_NAME=ecole-platform-uploads
```

## Development Setup

MinIO is automatically started by `docker-compose.dev.yml`:

```bash
docker-compose -f infra/docker-compose.dev.yml up minio minio-init
```

### Default Credentials (Development Only)
- Access Key: `minioadmin`
- Secret Key: `minioadmin`
- Console URL: http://localhost:9001
- API Endpoint: http://localhost:9000

### Buckets Created

The `minio-init` container creates:
- `ecole-uploads` — Main file storage bucket
- ILM rules applied for automatic cleanup:
  - Submissions: 730 days retention
  - Document previews: 30 days retention
  - Reports: 7 days retention

## Migrating to External S3

When moving from development (MinIO) to production (S3):

1. Update `STORAGE_BACKEND=s3` in environment
2. Configure S3 credentials
3. Update `S3_ENDPOINT` to your provider
4. Run `scripts/migrate_local_to_minio.py` if migrating existing files

## Security Notes

- **Never use default MinIO credentials in production**
- MinIO in dev uses a hardcoded KMS key (acceptable for local development only)
- Production must use provider-managed encryption (SSE-S3 or SSE-KMS)

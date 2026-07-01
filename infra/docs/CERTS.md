# TLS/SSL Certificates

Directory for storing TLS/SSL certificates used in production and staging environments. Certificates are excluded from git for security.

## Purpose

This directory holds:
- Production HTTPS certificates
- Staging certificates for testing
- Certificate authority (CA) bundles
- Private keys (never commit to git)

## Files Included

- **.gitignore** - Excludes all certificate files from version control

## Certificate Storage

Place certificates here following this structure:
```
certs/
├── prod/
│   ├── ecole-platform.crt
│   ├── ecole-platform.key
│   └── ca-bundle.crt
├── staging/
│   ├── staging.ecole.crt
│   └── staging.ecole.key
└── dhparam.pem
```

## Security

Never commit certificate files or private keys to git. The `.gitignore` prevents accidental commits.

For local development with self-signed certs:
```bash
openssl req -x509 -newkey rsa:2048 -keyout dev.key -out dev.crt -days 365 -nodes
```

## Certificate Renewal

Automated renewal via:
```bash
../scripts/ssl-renew.sh
```

Supports both:
- Let's Encrypt ACME protocol (recommended for production)
- Manual certificate import

See `../DEPLOYMENT.md` for renewal configuration and frequency.

## Docker Integration

Certificates are mounted in Docker containers via:
```yaml
volumes:
  - ./certs/prod:/etc/nginx/certs:ro
```

Only exposed to nginx reverse proxy container.

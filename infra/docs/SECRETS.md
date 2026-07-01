# Docker Secrets

Never commit anything in this directory. Generate unique secrets for each environment and store them in separate secret files.

## Generate Secrets

```bash
# JWT signing key
openssl rand -hex 32 > jwt_secret_key.txt

# PostgreSQL superuser password
openssl rand -base64 24 > db_password.txt

# Application database role passwords
openssl rand -base64 24 > app_db_password.txt
openssl rand -base64 24 > app_readonly_password.txt

# Redis password
openssl rand -base64 24 > redis_password.txt

# SMTP password
printf '%s' 'replace-with-your-smtp-password' > smtp_password.txt
```

## Derived Secret Files

Create full connection-string secrets from the generated passwords:

```bash
printf 'postgresql+asyncpg://ecole:%s@postgres:5432/ecole_platform' "$(cat db_password.txt)" > database_url.txt
printf 'redis://:%s@redis:6379/0' "$(cat redis_password.txt)" > redis_url.txt
```

## Where Each Secret Goes

- `jwt_secret_key.txt`: production backend and worker `JWT_SECRET_KEY_FILE`
- `db_password.txt`: PostgreSQL superuser `POSTGRES_PASSWORD_FILE`
- `app_db_password.txt`: PostgreSQL init role `APP_DB_PASSWORD_FILE`
- `app_readonly_password.txt`: PostgreSQL init role `APP_READONLY_PASSWORD_FILE`
- `database_url.txt`: backend and worker `DATABASE_URL_FILE`
- `redis_password.txt`: Redis server auth and health checks
- `redis_url.txt`: backend and worker `REDIS_URL_FILE`
- `smtp_password.txt`: backend and worker `SMTP_PASSWORD_FILE`

## Environment Guidance

- Development: keep secrets in local `.env` only and rotate if they were ever committed.
- Staging: generate a separate full set of files with different values from development.
- Production: generate a separate full set of files again, mount them as Docker secrets, and never reuse staging credentials.

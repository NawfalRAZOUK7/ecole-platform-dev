-- École Platform — PostgreSQL Initialization
-- Reference: Pack C4 (Data Model), Pack D4 (Database Strategy)
--
-- Domains: IAM, ERP, LMS, COM, Billing, IA/Audit
-- All tables use public schema (V1 single-schema approach per D4)
-- Domain separation through table naming convention

\set app_user_password `sh -c 'if [ -n "${APP_DB_PASSWORD_FILE:-}" ] && [ -f "${APP_DB_PASSWORD_FILE}" ]; then cat "${APP_DB_PASSWORD_FILE}"; else printf "%s" "${APP_DB_PASSWORD:-change-me-app-user}"; fi'`
\set app_readonly_password `sh -c 'if [ -n "${APP_READONLY_PASSWORD_FILE:-}" ] && [ -f "${APP_READONLY_PASSWORD_FILE}" ]; then cat "${APP_READONLY_PASSWORD_FILE}"; else printf "%s" "${APP_READONLY_PASSWORD:-change-me-readonly}"; fi'`

-- Create application roles with environment-specific passwords
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        EXECUTE format('CREATE ROLE app_user WITH LOGIN PASSWORD %L', :'app_user_password');
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_readonly') THEN
        EXECUTE format('CREATE ROLE app_readonly WITH LOGIN PASSWORD %L', :'app_readonly_password');
    END IF;
END
$$;

-- Grant privileges on the current application database
DO $$
BEGIN
    EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO app_user', current_database());
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO app_readonly', current_database());
END
$$;

GRANT USAGE, CREATE ON SCHEMA public TO app_user;
GRANT USAGE ON SCHEMA public TO app_readonly;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO app_readonly;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Domain documentation (comments for schema documentation)
COMMENT ON DATABASE ecole_platform IS 'École Platform — EdTech SaaS for K-12 schools';

-- Tables will be created by Alembic migrations (Sprint 1, S-014 through S-019)
-- Migration order: G1-IAM → G2-ERP → G3-LMS → G4-COM → G5-Billing → G6-IA/Audit

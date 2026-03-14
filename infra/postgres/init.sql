-- École Platform — PostgreSQL Initialization
-- Reference: Pack C4 (Data Model), Pack D4 (Database Strategy)
--
-- Domains: IAM, ERP, LMS, COM, Billing, IA/Audit
-- All tables use public schema (V1 single-schema approach per D4)
-- Domain separation through table naming convention

-- Create application roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'ecole';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_readonly') THEN
        CREATE ROLE app_readonly WITH LOGIN PASSWORD 'ecole_ro';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ecole_platform TO app_user;
GRANT CONNECT ON DATABASE ecole_platform TO app_readonly;

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

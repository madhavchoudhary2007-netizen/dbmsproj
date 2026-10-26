-- Phase 4 DBMS Showcase: Roles, Grants, and Row Level Security (RLS)

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apexgrid_app') THEN
        CREATE ROLE apexgrid_app NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'apexgrid_readonly') THEN
        CREATE ROLE apexgrid_readonly NOLOGIN;
    END IF;
END $$;

-- Grant DML privileges to apexgrid_app
GRANT USAGE ON SCHEMA public TO apexgrid_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO apexgrid_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO apexgrid_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO apexgrid_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO apexgrid_app;

-- Grant Read-Only privileges to apexgrid_readonly
GRANT USAGE ON SCHEMA public TO apexgrid_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO apexgrid_readonly;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO apexgrid_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO apexgrid_readonly;

-- Row Level Security on audit_log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS audit_stewards_penalties ON audit_log;
CREATE POLICY audit_stewards_penalties ON audit_log
    FOR ALL
    USING (
        current_setting('apexgrid.role', true) IN ('admin', 'steward', 'director')
        OR current_user = 'apexgrid'
    );

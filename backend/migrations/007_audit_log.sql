-- Phase 4 DBMS Showcase: Generic Audit Logging and Change Data Capture

CREATE TABLE IF NOT EXISTS audit_log (
    id bigserial PRIMARY KEY,
    table_name text NOT NULL,
    op text NOT NULL,
    row_pk jsonb,
    old jsonb,
    new jsonb,
    actor text,
    at timestamptz DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_at ON audit_log (table_name, at DESC);

CREATE OR REPLACE FUNCTION audit_row() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_actor text;
    v_pk jsonb;
    v_old jsonb;
    v_new jsonb;
BEGIN
    BEGIN
        v_actor := nullif(current_setting('apexgrid.actor', true), '');
    EXCEPTION WHEN OTHERS THEN
        v_actor := NULL;
    END;

    IF TG_OP = 'DELETE' THEN
        v_old := to_jsonb(OLD);
        v_new := NULL;
        IF v_old ? 'id' THEN
            v_pk := jsonb_build_object('id', v_old->'id');
        ELSE
            v_pk := v_old;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
        IF v_new ? 'id' THEN
            v_pk := jsonb_build_object('id', v_new->'id');
        ELSE
            v_pk := v_new;
        END IF;
    ELSIF TG_OP = 'INSERT' THEN
        v_old := NULL;
        v_new := to_jsonb(NEW);
        IF v_new ? 'id' THEN
            v_pk := jsonb_build_object('id', v_new->'id');
        ELSE
            v_pk := v_new;
        END IF;
    END IF;

    INSERT INTO audit_log (table_name, op, row_pk, old, new, actor, at)
    VALUES (TG_TABLE_NAME, TG_OP, v_pk, v_old, v_new, v_actor, clock_timestamp());

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END $$;

-- Attach triggers to target tables
DROP TRIGGER IF EXISTS trg_audit_penalties ON penalties;
CREATE TRIGGER trg_audit_penalties AFTER INSERT OR UPDATE OR DELETE ON penalties
FOR EACH ROW EXECUTE FUNCTION audit_row();

DROP TRIGGER IF EXISTS trg_audit_pit_reservations ON pit_reservations;
CREATE TRIGGER trg_audit_pit_reservations AFTER INSERT OR UPDATE OR DELETE ON pit_reservations
FOR EACH ROW EXECUTE FUNCTION audit_row();

DROP TRIGGER IF EXISTS trg_audit_championships ON championships;
CREATE TRIGGER trg_audit_championships AFTER INSERT OR UPDATE OR DELETE ON championships
FOR EACH ROW EXECUTE FUNCTION audit_row();

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='session_results') THEN
        DROP TRIGGER IF EXISTS trg_audit_session_results ON session_results;
        CREATE TRIGGER trg_audit_session_results AFTER INSERT OR UPDATE OR DELETE ON session_results
        FOR EACH ROW EXECUTE FUNCTION audit_row();
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='results') THEN
        DROP TRIGGER IF EXISTS trg_audit_results ON results;
        CREATE TRIGGER trg_audit_results AFTER INSERT OR UPDATE OR DELETE ON results
        FOR EACH ROW EXECUTE FUNCTION audit_row();
    END IF;
END $$;

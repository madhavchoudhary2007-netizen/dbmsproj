-- Restrict steward audit visibility to penalty rows while preserving the
-- existing admin, director, and table-owner access for audit operations.
DROP POLICY IF EXISTS audit_stewards_penalties ON audit_log;
CREATE POLICY audit_stewards_penalties ON audit_log
    FOR ALL
    USING (
        current_user = 'apexgrid'
        OR current_setting('apexgrid.role', true) IN ('admin', 'director')
        OR (
            current_setting('apexgrid.role', true) = 'steward'
            AND table_name = 'penalties'
        )
    )
    WITH CHECK (
        current_user = 'apexgrid'
        OR current_setting('apexgrid.role', true) IN ('admin', 'director')
        OR (
            current_setting('apexgrid.role', true) = 'steward'
            AND table_name = 'penalties'
        )
    );

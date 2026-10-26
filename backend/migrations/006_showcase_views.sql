-- Phase 4 DBMS Showcase: Views and Materialized Views (ADR-009)

-- Regular view: driver season summary across championships
CREATE OR REPLACE VIEW v_driver_season_summary AS
SELECT
    ds.driver_id,
    d.number AS driver_number,
    c.id AS championship_id,
    c.name AS championship_name,
    c.season,
    ds.points,
    ds.wins,
    ds.podiums,
    ds.rank
FROM driver_standings ds
JOIN championships c ON c.id = ds.championship_id
LEFT JOIN drivers d ON d.id = ds.driver_id;

-- Materialized view: championship standings rollup
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_championship_standings AS
SELECT
    ds.championship_id,
    ds.driver_id,
    ds.points,
    ds.wins,
    ds.podiums,
    ds.rank,
    c.name AS championship_name,
    c.season
FROM driver_standings ds
JOIN championships c ON c.id = ds.championship_id;

-- Unique index required for REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_championship_standings
ON mv_championship_standings (championship_id, driver_id);

-- Dynamic points systems configuration (ADR-009)
CREATE TABLE IF NOT EXISTS points_systems (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name varchar(64) NOT NULL UNIQUE,
  is_default boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS points_system_positions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  system_id uuid NOT NULL REFERENCES points_systems(id) ON DELETE CASCADE,
  position integer NOT NULL,
  points integer NOT NULL,
  CONSTRAINT uq_points_system_position UNIQUE(system_id, position)
);

-- Seed default F1 2025 system
INSERT INTO points_systems (id, name, is_default)
VALUES ('00000000-0000-0000-0000-000000000001'::uuid, 'FIA Formula 1 Standard (2025)', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO points_system_positions (system_id, position, points)
VALUES
  ('00000000-0000-0000-0000-000000000001'::uuid, 1, 25),
  ('00000000-0000-0000-0000-000000000001'::uuid, 2, 18),
  ('00000000-0000-0000-0000-000000000001'::uuid, 3, 15),
  ('00000000-0000-0000-0000-000000000001'::uuid, 4, 12),
  ('00000000-0000-0000-0000-000000000001'::uuid, 5, 10),
  ('00000000-0000-0000-0000-000000000001'::uuid, 6, 8),
  ('00000000-0000-0000-0000-000000000001'::uuid, 7, 6),
  ('00000000-0000-0000-0000-000000000001'::uuid, 8, 4),
  ('00000000-0000-0000-0000-000000000001'::uuid, 9, 2),
  ('00000000-0000-0000-0000-000000000001'::uuid, 10, 1)
ON CONFLICT (system_id, position) DO NOTHING;

ALTER TABLE championships
  ADD COLUMN IF NOT EXISTS points_system_id uuid REFERENCES points_systems(id) DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;

UPDATE championships
SET points_system_id = '00000000-0000-0000-0000-000000000001'::uuid
WHERE points_system_id IS NULL;

-- Dynamic recalculate_standings function joining points system positions
CREATE OR REPLACE FUNCTION recalculate_standings(p_championship_id uuid) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE rec record;
DECLARE standings_cursor CURSOR FOR
 SELECT r.driver_id,
   sum(CASE
     WHEN NOT r.classified THEN 0
     WHEN c.points_system_id IS NOT NULL THEN COALESCE(psp.points, 0)
     WHEN r.position=1 THEN 25 WHEN r.position=2 THEN 18
     WHEN r.position=3 THEN 15 WHEN r.position=4 THEN 12
     WHEN r.position=5 THEN 10 WHEN r.position=6 THEN 8
     WHEN r.position=7 THEN 6 WHEN r.position=8 THEN 4
     WHEN r.position=9 THEN 2 WHEN r.position=10 THEN 1 ELSE 0 END
     + CASE WHEN r.classified AND r.pole THEN 1 ELSE 0 END
     + CASE WHEN r.classified AND r.fastest_lap THEN 1 ELSE 0 END)::integer AS total_points,
   count(*) FILTER(WHERE r.classified AND r.position=1)::integer AS wins,
   count(*) FILTER(WHERE r.classified AND r.position BETWEEN 1 AND 3)::integer AS podiums
 FROM session_results r
 JOIN race_sessions s ON s.id=r.session_id
 JOIN race_events e ON e.id=s.event_id
 JOIN championships c ON c.id=e.championship_id
 LEFT JOIN points_system_positions psp ON psp.system_id=c.points_system_id AND psp.position=r.position
 WHERE e.championship_id=p_championship_id AND s.session_type='RACE' AND s.state='COMPLETED'
 GROUP BY r.driver_id;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM championships WHERE id=p_championship_id) THEN
   RAISE EXCEPTION 'Championship % does not exist',p_championship_id USING ERRCODE='23503';
 END IF;
 DELETE FROM driver_standings WHERE championship_id=p_championship_id;
 CREATE TEMP TABLE IF NOT EXISTS _apexgrid_standings_work(
   driver_id uuid PRIMARY KEY, points integer, wins integer, podiums integer
 ) ON COMMIT DROP;
 TRUNCATE _apexgrid_standings_work;
 OPEN standings_cursor;
 LOOP
   FETCH standings_cursor INTO rec;
   EXIT WHEN NOT FOUND;
   INSERT INTO _apexgrid_standings_work VALUES(rec.driver_id,rec.total_points,rec.wins,rec.podiums);
 END LOOP;
 CLOSE standings_cursor;
 INSERT INTO driver_standings(championship_id,driver_id,points,wins,podiums,rank)
 SELECT p_championship_id,driver_id,points,wins,podiums,
   row_number() OVER(ORDER BY points DESC,wins DESC,podiums DESC,driver_id)::integer
 FROM _apexgrid_standings_work;
END $$;

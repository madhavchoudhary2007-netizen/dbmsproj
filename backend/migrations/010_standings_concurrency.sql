-- Serialize standings replacement for each championship without blocking others.
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
 PERFORM 1 FROM championships WHERE id=p_championship_id FOR UPDATE;
 IF NOT FOUND THEN
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

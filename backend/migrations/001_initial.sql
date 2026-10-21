-- ApexGrid relational foundation. Safe to re-run on an existing ApexGrid schema.
-- Standalone setup: psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/migrations/001_initial.sql
-- Then load development fixtures with: psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/db/seed.sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$ BEGIN CREATE TYPE user_role AS ENUM ('ADMIN','STEWARD','PRINCIPAL','DRIVER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE driver_eligibility AS ENUM ('ACTIVE','RACE_BANNED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE session_state AS ENUM ('SCHEDULED','ACTIVE','PAUSED','COMPLETED','CANCELLED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE session_type AS ENUM ('PRACTICE','QUALIFYING','RACE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE incident_state AS ENUM ('OPEN','APPROVED','REJECTED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE tire_compound AS ENUM ('SOFT','MEDIUM','HARD','INTERMEDIATE','WET'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE reservation_status AS ENUM ('RESERVED','CANCELLED','COMPLETED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), email text NOT NULL UNIQUE,
 password_hash text NOT NULL, full_name text NOT NULL, role user_role NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), CHECK (length(trim(email)) > 3), CHECK (length(trim(full_name)) > 0)
);
CREATE TABLE IF NOT EXISTS teams (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE,
 principal_user_id uuid REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS drivers (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid UNIQUE REFERENCES users(id) ON DELETE SET NULL,
 licence_number text NOT NULL UNIQUE, number integer NOT NULL CHECK (number BETWEEN 1 AND 999),
 eligibility driver_eligibility NOT NULL DEFAULT 'ACTIVE'
);
-- Car numbers are unique within a generated grid, but may be reused by drivers
-- in later race archives. A global uniqueness constraint eventually exhausted
-- plausible two-digit numbers as the automatic race kept completed sessions.
ALTER TABLE drivers DROP CONSTRAINT IF EXISTS drivers_number_key;
CREATE INDEX IF NOT EXISTS idx_drivers_number ON drivers(number);
CREATE TABLE IF NOT EXISTS team_memberships (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
 team_id uuid NOT NULL REFERENCES teams(id) ON DELETE CASCADE, start_date date NOT NULL, end_date date,
 CHECK (end_date IS NULL OR end_date >= start_date), UNIQUE (driver_id, team_id, start_date)
);
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='team_memberships'::regclass AND conname='team_memberships_no_driver_overlap') THEN
  ALTER TABLE team_memberships ADD CONSTRAINT team_memberships_no_driver_overlap
   EXCLUDE USING gist (driver_id WITH =,
    daterange(start_date,CASE WHEN end_date IS NULL THEN 'infinity'::date ELSE end_date+1 END,'[)') WITH &&);
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS championships (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL, season integer NOT NULL CHECK (season BETWEEN 1900 AND 9999),
 UNIQUE(name,season)
);
CREATE TABLE IF NOT EXISTS circuits (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE, country text NOT NULL,
 length_km numeric(7,3) NOT NULL CHECK(length_km > 0)
);
CREATE TABLE IF NOT EXISTS race_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), championship_id uuid NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
 circuit_id uuid NOT NULL REFERENCES circuits(id) ON DELETE RESTRICT, round_number integer NOT NULL CHECK(round_number > 0),
 name text NOT NULL, start_date timestamptz NOT NULL, UNIQUE(championship_id,round_number)
);
CREATE TABLE IF NOT EXISTS race_sessions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), event_id uuid NOT NULL REFERENCES race_events(id) ON DELETE CASCADE,
 session_type session_type NOT NULL, state session_state NOT NULL DEFAULT 'SCHEDULED', scheduled_at timestamptz NOT NULL,
 started_at timestamptz, ended_at timestamptz, total_laps integer NOT NULL DEFAULT 0 CHECK(total_laps >= 0 AND total_laps<=72),
 safety_car boolean NOT NULL DEFAULT false,
 CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at)
);
-- Normalize legacy over-limit sessions before enforcing the new maximum.
UPDATE race_sessions SET total_laps=72 WHERE total_laps>72;
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='race_sessions'::regclass AND conname='race_sessions_total_laps_max_check') THEN
  ALTER TABLE race_sessions ADD CONSTRAINT race_sessions_total_laps_max_check CHECK (total_laps<=72);
 END IF;
END $$;
-- Supports a composite FK so a generated race cannot point at a different event
-- than its session. The primary key already guarantees id uniqueness.
CREATE UNIQUE INDEX IF NOT EXISTS idx_race_sessions_id_event ON race_sessions(id,event_id);
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='race_sessions'::regclass AND conname='race_sessions_state_timestamps_check') THEN
  ALTER TABLE race_sessions ADD CONSTRAINT race_sessions_state_timestamps_check CHECK (
   (state='SCHEDULED' AND started_at IS NULL AND ended_at IS NULL) OR
   (state IN ('ACTIVE','PAUSED') AND started_at IS NOT NULL AND ended_at IS NULL) OR
   (state='COMPLETED' AND started_at IS NOT NULL AND ended_at IS NOT NULL AND ended_at>=started_at) OR
   (state='CANCELLED' AND ((started_at IS NULL AND ended_at IS NULL) OR
     (started_at IS NOT NULL AND (ended_at IS NULL OR ended_at>=started_at))))
  );
 END IF;
END $$;
CREATE OR REPLACE FUNCTION enforce_race_session_transition() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_allowed boolean := true;
BEGIN
 IF TG_OP='UPDATE' AND NEW.state IS DISTINCT FROM OLD.state THEN
  v_allowed := CASE OLD.state
   WHEN 'SCHEDULED' THEN NEW.state IN ('ACTIVE','CANCELLED')
   WHEN 'ACTIVE' THEN NEW.state IN ('PAUSED','COMPLETED','SCHEDULED','CANCELLED')
   WHEN 'PAUSED' THEN NEW.state IN ('ACTIVE','COMPLETED','SCHEDULED','CANCELLED')
   WHEN 'COMPLETED' THEN NEW.state IN ('SCHEDULED','CANCELLED')
   WHEN 'CANCELLED' THEN NEW.state='SCHEDULED'
  END;
  IF NOT v_allowed THEN
   RAISE EXCEPTION 'Invalid race session transition: % -> %',OLD.state,NEW.state USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_race_session_transition ON race_sessions;
CREATE TRIGGER trg_race_session_transition BEFORE INSERT OR UPDATE ON race_sessions
 FOR EACH ROW EXECUTE FUNCTION enforce_race_session_transition();
CREATE TABLE IF NOT EXISTS incident_reports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), session_id uuid NOT NULL REFERENCES race_sessions(id) ON DELETE CASCADE,
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT, lap integer NOT NULL CHECK(lap > 0),
 description text NOT NULL CHECK(length(trim(description)) > 0), state incident_state NOT NULL DEFAULT 'OPEN',
 reported_at timestamptz NOT NULL DEFAULT now(), decided_by uuid REFERENCES users(id) ON DELETE SET NULL, decision_notes text
);
-- Keep incident references inside the recorded race distance. A zero-lap
-- session is an unspecified-distance session, but incidents still cannot
-- exceed the simulator's hard 72-lap limit.
CREATE OR REPLACE FUNCTION enforce_incident_lap_limit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_total_laps integer;
BEGIN
 SELECT total_laps INTO v_total_laps FROM race_sessions WHERE id=NEW.session_id;
 IF NEW.lap>72 OR (v_total_laps>0 AND NEW.lap>v_total_laps) THEN
   RAISE EXCEPTION 'Incident lap % exceeds session distance %',NEW.lap,v_total_laps USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_incident_lap_limit ON incident_reports;
CREATE TRIGGER trg_incident_lap_limit BEFORE INSERT OR UPDATE OF session_id,lap ON incident_reports
 FOR EACH ROW EXECUTE FUNCTION enforce_incident_lap_limit();
CREATE OR REPLACE FUNCTION prevent_session_distance_below_incidents() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.total_laps>0 AND EXISTS(SELECT 1 FROM incident_reports WHERE session_id=NEW.id AND lap>NEW.total_laps) THEN
   RAISE EXCEPTION 'Session distance cannot be reduced below a recorded incident lap' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_session_distance_incidents ON race_sessions;
CREATE TRIGGER trg_session_distance_incidents BEFORE UPDATE OF total_laps ON race_sessions
 FOR EACH ROW EXECUTE FUNCTION prevent_session_distance_below_incidents();
CREATE TABLE IF NOT EXISTS demo_races (
 session_id uuid PRIMARY KEY REFERENCES race_sessions(id) ON DELETE CASCADE,
 event_id uuid NOT NULL REFERENCES race_events(id) ON DELETE CASCADE,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (session_id,event_id) REFERENCES race_sessions(id,event_id) ON DELETE CASCADE
);
ALTER TABLE demo_races ADD COLUMN IF NOT EXISTS auto_repeat boolean NOT NULL DEFAULT false;
CREATE TABLE IF NOT EXISTS demo_race_entries (
 session_id uuid NOT NULL REFERENCES demo_races(session_id) ON DELETE CASCADE,
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT,
 pace_offset_ms integer NOT NULL CHECK (pace_offset_ms BETWEEN -2000 AND 3000),
 PRIMARY KEY (session_id,driver_id)
);
CREATE TABLE IF NOT EXISTS penalties (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), incident_id uuid NOT NULL UNIQUE REFERENCES incident_reports(id) ON DELETE RESTRICT,
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT,
 points integer NOT NULL DEFAULT 0 CHECK(points >= 0), time_seconds integer NOT NULL DEFAULT 0 CHECK(time_seconds >= 0),
 grid_places integer NOT NULL DEFAULT 0 CHECK(grid_places >= 0), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS penalty_points (
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE CASCADE, season integer NOT NULL CHECK(season BETWEEN 1900 AND 9999),
 points integer NOT NULL DEFAULT 0 CHECK(points >= 0), PRIMARY KEY(driver_id,season)
);
CREATE TABLE IF NOT EXISTS session_results (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), session_id uuid NOT NULL REFERENCES race_sessions(id) ON DELETE CASCADE,
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT, position integer CHECK(position > 0),
 lap_time_ms integer CHECK(lap_time_ms > 0), pole boolean NOT NULL DEFAULT false, fastest_lap boolean NOT NULL DEFAULT false,
 classified boolean NOT NULL DEFAULT true, UNIQUE(session_id,driver_id)
);
CREATE TABLE IF NOT EXISTS driver_standings (
 championship_id uuid NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
 driver_id uuid NOT NULL REFERENCES drivers(id) ON DELETE CASCADE, points integer NOT NULL DEFAULT 0 CHECK(points >= 0),
 wins integer NOT NULL DEFAULT 0 CHECK(wins >= 0), podiums integer NOT NULL DEFAULT 0 CHECK(podiums >= 0),
 rank integer NOT NULL CHECK(rank > 0), PRIMARY KEY(championship_id,driver_id), UNIQUE(championship_id,rank)
);
CREATE TABLE IF NOT EXISTS pit_boxes (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), event_id uuid NOT NULL REFERENCES race_events(id) ON DELETE CASCADE,
 number integer NOT NULL CHECK(number > 0), UNIQUE(event_id,number), UNIQUE(id,event_id)
);
-- Generated demo events get a small pit wall; this is idempotent and never changes existing boxes.
INSERT INTO pit_boxes(event_id,number)
 SELECT d.event_id,n FROM demo_races d CROSS JOIN generate_series(1,4) AS n
 ON CONFLICT(event_id,number) DO NOTHING;
CREATE TABLE IF NOT EXISTS pit_reservations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), pit_box_id uuid NOT NULL REFERENCES pit_boxes(id) ON DELETE RESTRICT,
 session_id uuid NOT NULL REFERENCES race_sessions(id) ON DELETE CASCADE, team_id uuid NOT NULL REFERENCES teams(id) ON DELETE RESTRICT,
 driver_id uuid REFERENCES drivers(id) ON DELETE RESTRICT,
 allocation_source text NOT NULL DEFAULT 'MANUAL' CHECK (allocation_source IN ('AUTOMATIC','MANUAL')),
 starts_at timestamptz NOT NULL, ends_at timestamptz NOT NULL, status reservation_status NOT NULL DEFAULT 'RESERVED',
 CHECK(ends_at > starts_at)
);
ALTER TABLE pit_reservations ADD COLUMN IF NOT EXISTS driver_id uuid REFERENCES drivers(id) ON DELETE RESTRICT;
ALTER TABLE pit_reservations ADD COLUMN IF NOT EXISTS allocation_source text NOT NULL DEFAULT 'MANUAL';
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='pit_reservations'::regclass AND conname='pit_reservations_allocation_source_check') THEN
  ALTER TABLE pit_reservations ADD CONSTRAINT pit_reservations_allocation_source_check CHECK (allocation_source IN ('AUTOMATIC','MANUAL'));
 END IF;
END $$;

-- Operations and common filters.
CREATE INDEX IF NOT EXISTS idx_session_results_session_lap_time ON session_results(session_id,lap_time_ms);
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_results_unique_classified_position
 ON session_results(session_id,position) WHERE classified AND position IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_drivers_licence_hash ON drivers USING hash(licence_number);
CREATE INDEX IF NOT EXISTS idx_events_championship ON race_events(championship_id,round_number);
CREATE INDEX IF NOT EXISTS idx_sessions_event_state ON race_sessions(event_id,state);
CREATE INDEX IF NOT EXISTS idx_incidents_session_state ON incident_reports(session_id,state);
CREATE INDEX IF NOT EXISTS idx_results_driver ON session_results(driver_id,session_id);
CREATE INDEX IF NOT EXISTS idx_reservations_session ON pit_reservations(session_id,status);
-- Replace the historical lookup-only index with the enforcing unique index.
-- DROP IF EXISTS also upgrades databases that already ran the earlier migration.
DROP INDEX IF EXISTS idx_pit_reservations_driver_active;
CREATE UNIQUE INDEX IF NOT EXISTS uq_pit_reservations_active_driver
 ON pit_reservations(session_id,driver_id) WHERE status='RESERVED' AND driver_id IS NOT NULL;
-- Overlap protection for active reservations. Half-open windows allow back-to-back bookings.
DO $$ BEGIN
 ALTER TABLE pit_reservations ADD CONSTRAINT pit_reservations_no_overlap
 EXCLUDE USING gist (pit_box_id WITH =, tstzrange(starts_at,ends_at,'[)') WITH &&)
 WHERE (status = 'RESERVED');
EXCEPTION WHEN duplicate_object OR duplicate_table THEN NULL; END $$;

-- Only newly inserted official penalties affect seasonal points. Unique incident_id prevents duplicate awards.
CREATE OR REPLACE FUNCTION apply_penalty_points() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_season integer;
DECLARE v_incident_driver uuid;
DECLARE v_incident_state incident_state;
BEGIN
 SELECT c.season,i.driver_id,i.state INTO v_season,v_incident_driver,v_incident_state
 FROM incident_reports i JOIN race_sessions s ON s.id=i.session_id
 JOIN race_events e ON e.id=s.event_id JOIN championships c ON c.id=e.championship_id
 WHERE i.id=NEW.incident_id;
 IF v_season IS NULL THEN RAISE EXCEPTION 'Cannot resolve championship season for incident %', NEW.incident_id; END IF;
 IF v_incident_state<>'APPROVED' THEN RAISE EXCEPTION 'Penalties require an approved incident' USING ERRCODE='23514'; END IF;
 IF v_incident_driver<>NEW.driver_id THEN RAISE EXCEPTION 'Penalty driver must match incident driver' USING ERRCODE='23514'; END IF;
 INSERT INTO penalty_points(driver_id,season,points) VALUES(NEW.driver_id,v_season,NEW.points)
 ON CONFLICT(driver_id,season) DO UPDATE SET points=penalty_points.points+EXCLUDED.points;
 IF (SELECT points FROM penalty_points WHERE driver_id=NEW.driver_id AND season=v_season) >= 12 THEN
   UPDATE drivers SET eligibility='RACE_BANNED' WHERE id=NEW.driver_id;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_penalty_points_after_insert ON penalties;
CREATE TRIGGER trg_penalty_points_after_insert AFTER INSERT ON penalties
 FOR EACH ROW EXECUTE FUNCTION apply_penalty_points();

-- Penalty points are an insert-only ledger. Prevent edits or removals from
-- making the source penalties disagree with the accumulated seasonal total.
CREATE OR REPLACE FUNCTION prevent_penalty_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'Official penalties are immutable' USING ERRCODE='23514';
END $$;
DROP TRIGGER IF EXISTS trg_penalties_immutable ON penalties;
CREATE TRIGGER trg_penalties_immutable BEFORE UPDATE OR DELETE ON penalties
 FOR EACH ROW EXECUTE FUNCTION prevent_penalty_mutation();

-- Explicit cursor over per-driver championship totals, then persist deterministic ranks.
CREATE OR REPLACE FUNCTION recalculate_standings(p_championship_id uuid) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE rec record;
DECLARE standings_cursor CURSOR FOR
 SELECT r.driver_id,
   sum(CASE WHEN r.classified AND r.position=1 THEN 25 WHEN r.classified AND r.position=2 THEN 18
     WHEN r.classified AND r.position=3 THEN 15 WHEN r.classified AND r.position=4 THEN 12
     WHEN r.classified AND r.position=5 THEN 10 WHEN r.classified AND r.position=6 THEN 8
     WHEN r.classified AND r.position=7 THEN 6 WHEN r.classified AND r.position=8 THEN 4
     WHEN r.classified AND r.position=9 THEN 2 WHEN r.classified AND r.position=10 THEN 1 ELSE 0 END
     + CASE WHEN r.pole THEN 1 ELSE 0 END + CASE WHEN r.fastest_lap THEN 1 ELSE 0 END)::integer AS total_points,
   count(*) FILTER(WHERE r.classified AND r.position=1)::integer AS wins,
   count(*) FILTER(WHERE r.classified AND r.position BETWEEN 1 AND 3)::integer AS podiums
 FROM session_results r JOIN race_sessions s ON s.id=r.session_id
 JOIN race_events e ON e.id=s.event_id
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

-- Caller must execute within a transaction and commit. Lock is held through caller commit.
CREATE OR REPLACE FUNCTION reserve_pit_box(
 p_pit_box_id uuid,p_session_id uuid,p_team_id uuid,p_starts_at timestamptz,p_ends_at timestamptz
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_reservation_id uuid;
DECLARE v_box_event uuid;
DECLARE v_session_event uuid;
BEGIN
 IF p_starts_at IS NULL OR p_ends_at IS NULL OR p_ends_at<=p_starts_at THEN
   RAISE EXCEPTION 'Reservation end must be after start' USING ERRCODE='22007';
 END IF;
 SELECT event_id INTO v_box_event FROM pit_boxes WHERE id=p_pit_box_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Pit box not found' USING ERRCODE='23503'; END IF;
 SELECT event_id INTO v_session_event FROM race_sessions WHERE id=p_session_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Session not found' USING ERRCODE='23503'; END IF;
 IF v_box_event<>v_session_event THEN RAISE EXCEPTION 'Pit box and session must belong to the same event' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT 1 FROM pit_reservations WHERE pit_box_id=p_pit_box_id AND status='RESERVED'
           AND tstzrange(starts_at,ends_at,'[)') && tstzrange(p_starts_at,p_ends_at,'[)')) THEN
   RAISE EXCEPTION 'Pit box reservation overlaps an existing reservation' USING ERRCODE='23P01';
 END IF;
 INSERT INTO pit_reservations(pit_box_id,session_id,team_id,starts_at,ends_at)
 VALUES(p_pit_box_id,p_session_id,p_team_id,p_starts_at,p_ends_at) RETURNING id INTO v_reservation_id;
 RETURN v_reservation_id;
END $$;

-- Allocate the earliest available box/window, including gaps before later bookings.
-- Locking the event serializes automatic allocations across its boxes.
CREATE OR REPLACE FUNCTION reserve_pit_box_auto(
 p_session_id uuid,p_team_id uuid,p_driver_id uuid,p_duration interval DEFAULT interval '5 minutes'
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_event_id uuid;
DECLARE v_session_state session_state;
DECLARE v_session_at timestamptz;
DECLARE v_driver_id uuid;
DECLARE v_box record;
DECLARE v_booking record;
DECLARE v_candidate timestamptz;
DECLARE v_best_start timestamptz;
DECLARE v_best_box uuid;
DECLARE v_reservation_id uuid;
BEGIN
 IF p_duration IS NULL OR p_duration<=interval '0' THEN
   RAISE EXCEPTION 'Reservation duration must be positive' USING ERRCODE='22023';
 END IF;
 SELECT event_id,state,COALESCE(started_at,scheduled_at) INTO v_event_id,v_session_state,v_session_at
 FROM race_sessions WHERE id=p_session_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Session not found' USING ERRCODE='23503'; END IF;
 IF v_session_state NOT IN ('ACTIVE','PAUSED') THEN
   RAISE EXCEPTION 'Automatic pit reservations require an active session' USING ERRCODE='23514';
 END IF;
 PERFORM 1 FROM race_events WHERE id=v_event_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Event not found' USING ERRCODE='23503'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pit_boxes WHERE event_id=v_event_id) THEN
   RAISE EXCEPTION 'Event has no pit boxes' USING ERRCODE='P0002';
 END IF;

 IF p_driver_id IS NULL THEN
   SELECT d.id INTO v_driver_id FROM drivers d
   JOIN team_memberships m ON m.driver_id=d.id AND m.team_id=p_team_id
   WHERE d.eligibility='ACTIVE' AND m.start_date<=v_session_at::date
     AND (m.end_date IS NULL OR m.end_date>=v_session_at::date)
     AND NOT EXISTS (SELECT 1 FROM pit_reservations pr WHERE pr.session_id=p_session_id
       AND pr.driver_id=d.id AND pr.status='RESERVED')
   ORDER BY d.number,d.id LIMIT 1;
   IF NOT FOUND THEN
     IF EXISTS (SELECT 1 FROM drivers d JOIN team_memberships m ON m.driver_id=d.id
       WHERE m.team_id=p_team_id AND d.eligibility='ACTIVE'
         AND m.start_date<=v_session_at::date AND (m.end_date IS NULL OR m.end_date>=v_session_at::date)) THEN
       RAISE EXCEPTION 'All eligible drivers already have an open pit reservation' USING ERRCODE='23505';
     END IF;
     RAISE EXCEPTION 'Team has no eligible driver for this session' USING ERRCODE='23514';
   END IF;
 ELSE
   v_driver_id:=p_driver_id;
   IF NOT EXISTS (SELECT 1 FROM drivers d JOIN team_memberships m ON m.driver_id=d.id
      WHERE d.id=v_driver_id AND d.eligibility='ACTIVE' AND m.team_id=p_team_id
        AND m.start_date<=v_session_at::date AND (m.end_date IS NULL OR m.end_date>=v_session_at::date)) THEN
     RAISE EXCEPTION 'Driver is not an eligible member of the team for this session' USING ERRCODE='23514';
   END IF;
 END IF;
 IF EXISTS (SELECT 1 FROM pit_reservations WHERE session_id=p_session_id AND driver_id=v_driver_id AND status='RESERVED') THEN
   RAISE EXCEPTION 'Driver already has an open pit reservation for this session' USING ERRCODE='23505';
 END IF;

 FOR v_box IN SELECT id FROM pit_boxes WHERE event_id=v_event_id ORDER BY number,id LOOP
   v_candidate:=GREATEST(now(),v_session_at);
   FOR v_booking IN SELECT starts_at,ends_at FROM pit_reservations
     WHERE pit_box_id=v_box.id AND status='RESERVED' AND ends_at>v_candidate
     ORDER BY starts_at,ends_at LOOP
     IF v_candidate+p_duration<=v_booking.starts_at THEN EXIT; END IF;
     IF v_booking.ends_at>v_candidate THEN v_candidate:=v_booking.ends_at; END IF;
   END LOOP;
   IF v_best_start IS NULL OR v_candidate<v_best_start THEN
     v_best_start:=v_candidate;
     v_best_box:=v_box.id;
   END IF;
 END LOOP;
 IF v_best_box IS NULL THEN RAISE EXCEPTION 'Event has no pit boxes' USING ERRCODE='P0002'; END IF;
 INSERT INTO pit_reservations(pit_box_id,session_id,team_id,driver_id,allocation_source,starts_at,ends_at)
 VALUES(v_best_box,p_session_id,p_team_id,v_driver_id,'AUTOMATIC',v_best_start,v_best_start+p_duration)
 RETURNING id INTO v_reservation_id;
 RETURN v_reservation_id;
END $$;

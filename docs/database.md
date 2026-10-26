# Database Design and Engineering Specification

Operator and schema specification for the ApexGrid polyglot persistence architecture. Antigravity and agent tasks use guarded disposable database instances (`apexgrid-test`) with scoped test transactions; production database credentials and volumes are never mutated.

---

## 1. Relational Normalisation & Schema Analysis

ApexGrid's relational schema is hosted on PostgreSQL 16. Official domain entities, transactions, financial/classification calculations, and audit logs reside in PostgreSQL.

### 1.1 Table Keys and Functional Dependencies

| Table | Primary Key | Candidate Keys | Key Functional Dependencies | Normal Form |
|---|---|---|---|---|
| `users` | `id` (UUID) | `email` | `id -> email, password_hash, full_name, role, is_active, created_at, updated_at` | BCNF |
| `championships` | `id` (UUID) | `code` | `id -> code, name, year, points_system_id, is_active` | BCNF |
| `circuits` | `id` (UUID) | `code` | `id -> code, name, country, city, length_km, turns` | BCNF |
| `teams` | `id` (UUID) | `(championship_id, name)` | `id -> championship_id, name, full_name, country, color_primary, color_secondary` | BCNF |
| `drivers` | `id` (UUID) | `code`, `user_id` | `id -> user_id, code, number, first_name, last_name, country, date_of_birth, is_active` | BCNF |
| `team_driver_memberships` | `id` (UUID) | `(team_id, driver_id, start_date)` | `id -> team_id, driver_id, start_date, end_date, role` | BCNF |
| `events` | `id` (UUID) | `(championship_id, round_number)` | `id -> championship_id, circuit_id, round_number, name, start_date, end_date` | BCNF |
| `race_sessions` | `id` (UUID) | none | `id -> event_id, name, session_type, status, scheduled_at, started_at, finished_at, total_laps` | BCNF |
| `pit_boxes` | `id` (UUID) | `(event_id, number)` | `id -> event_id, number, location` | BCNF |
| `pit_reservations` | `id` (UUID) | none | `id -> pit_box_id, session_id, team_id, window_start, window_end, status` | BCNF |
| `laps` | `id` (UUID) | `(session_id, driver_id, lap_number)` | `id -> session_id, driver_id, lap_number, lap_time_ms, sector_1_ms, sector_2_ms, sector_3_ms` | BCNF |
| `results` | `id` (UUID) | `(session_id, driver_id)` | `id -> session_id, driver_id, position, status, points, laps_completed, total_time_ms` | BCNF |
| `penalties` | `id` (UUID) | none | `id -> session_id, driver_id, incident_type, penalty_type, seconds_penalty, status` | BCNF |
| `points_systems` | `id` (UUID) | `code` | `id -> code, name, description` | BCNF |
| `points_system_positions` | `id` (UUID) | `(points_system_id, position)` | `id -> points_system_id, position, points` | BCNF |
| `audit_log` | `id` (BIGSERIAL) | none | `id -> table_name, op, row_pk, old, new, actor, at` | BCNF |

### 1.2 3NF / BCNF Justification

Every determinant in the relational schema is a candidate key. Transitive dependencies are eliminated through entity decomposition:
- **Driver and Team decoupling**: A driver does not belong directly to a team on the `drivers` table; the many-to-many relationship is modelled through `team_driver_memberships`, capturing contract windows (`start_date`, `end_date`) and avoiding update anomalies when drivers transfer teams between seasons.
- **Points system as data**: Points rules are separated from `championships` into `points_systems` and `points_system_positions` (migration `005_points_systems.sql`), eliminating hardcoded procedural assumptions.
- **Pit reservations range locking**: Reservations prevent double-booking via transactional exclusion and `reserve_pit_box` stored functions with row locks.

---

## 2. Deliberate Denormalisations

1. **MongoDB Telemetry Packets**:
   - High-rate car sensor telemetry (~100 Hz per car: throttle, brake, speed, RPM, gear, tyre temps, suspension travel, sector times) is captured as JSON documents in MongoDB's `telemetry` collection.
   - *Rationale*: Storing 20 cars × 100 Hz = 2,000 inserts/sec in PostgreSQL would induce write amplification, WAL churn, and lock contention on active race session tables. MongoDB handles schemaless high-frequency append streams with background flush and TTL indexing.
2. **Materialized View `mv_championship_standings`**:
   - Aggregates driver championship points, race counts, podiums, and ranking across all completed events in a season.
   - *Rationale*: Recomputing dynamic standings on every dashboard or standings view page load requires joining `results`, `race_sessions`, `events`, `championships`, and `drivers`. The materialized view precomputes this data with `CREATE UNIQUE INDEX uq_mv_championship_standings ON mv_championship_standings (championship_id, driver_id)`.
   - *Concurrency*: Updated using `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_championship_standings`, allowing concurrent read operations without blocking queries.

---

## 3. Index Rationale

| Table | Index Name | Columns / Type | Query Pattern Supported | Rationale |
|---|---|---|---|---|
| `laps` | `idx_laps_session_lap` | `(session_id, lap_number)` B-Tree | `WHERE session_id = ? ORDER BY lap_number` | Fast lap progression queries and window function partitions. |
| `laps` | `idx_laps_session_driver_lap` | `(session_id, driver_id, lap_number)` B-Tree | Driver lap history lookups | Fast retrieval of specific driver sector times and lap history. |
| `results` | `idx_results_session_pos` | `(session_id, position)` B-Tree | Running order and podium queries | Avoids sequential scans when rendering race classification tables. |
| `pit_reservations` | `idx_pit_reservations_window` | `(pit_box_id, window_start, window_end)` B-Tree | Overlap conflict checks | Critical for lock-demo and reservation conflict detection. |
| `mv_championship_standings` | `uq_mv_championship_standings` | `(championship_id, driver_id)` Unique B-Tree | `REFRESH MATERIALIZED VIEW CONCURRENTLY` | PostgreSQL requires a unique index on all columns or a primary key to refresh concurrently without locks. |
| `audit_log` | `idx_audit_log_table_at` | `(table_name, at DESC)` B-Tree | `WHERE table_name = ? ORDER BY at DESC` | Fast filtering of recent audit trail events for stewards. |
| `telemetry` (Mongo) | compound index | `session_id: 1, driver_id: 1, recorded_at: -1` | Driver telemetry timeline streaming | Enables index-covered sort for real-time pit wall charts. |

---

## 4. Backup & Restore Runbook

### 4.1 PostgreSQL Backup (Custom Format)

Generate an archive of the PostgreSQL database:
```bash
pg_dump -Fc -h localhost -U apexgrid -d apexgrid > backup_apexgrid_$(date +%Y%m%d_%H%M%S).dump
```

To back up only specific showcase views or tables:
```bash
pg_dump -Fc -h localhost -U apexgrid -t audit_log -t results apexgrid > backup_audit_$(date +%Y%m%d).dump
```

### 4.2 PostgreSQL Restore

Restore into an existing or clean database:
```bash
pg_restore -h localhost -U apexgrid -d apexgrid --clean --if-exists backup_apexgrid_*.dump
```

### 4.3 MongoDB Backup (Gzip Archive)

Export the MongoDB telemetry database:
```bash
mongodump --uri="mongodb://localhost:27017/apexgrid" --gzip --archive=backup_mongo_$(date +%Y%m%d_%H%M%S).gz
```

### 4.4 MongoDB Restore

Restore telemetry documents with drop-before-restore:
```bash
mongorestore --uri="mongodb://localhost:27017/apexgrid" --gzip --drop --archive=backup_mongo_*.gz
```

---

## 5. Security & Least Privilege

- **Role `apexgrid_app`**: Granted `SELECT, INSERT, UPDATE, DELETE` on application tables and sequences in schema `public`. Cannot execute DDL (`DROP`, `ALTER`, `CREATE`).
- **Role `apexgrid_readonly`**: Granted `SELECT` only on application tables. Used for analytical reporting and public telemetry mirrors.
- **Row-Level Security (RLS)**: Enabled on `audit_log` table. Stewards observe penalty changes, while administrators access system-wide audit records.

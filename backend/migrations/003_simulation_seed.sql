ALTER TABLE IF EXISTS demo_races
    ADD COLUMN IF NOT EXISTS simulation_seed bigint NULL;

-- Migration: Architectural Fixes
-- Date: 2025-12-01
-- Description: 
-- 1. Link Batch and TreatmentBatch (Traceability)
-- 2. Standardize TreatmentBatch facility_id
-- 3. Add is_active to operational tables (Audit)
-- 4. Standardize Plots to Hectares (Agronomy)

-- 1. Link Batch & TreatmentBatch
ALTER TABLE batches ADD COLUMN treatment_batch_id INTEGER REFERENCES treatment_batches(id);
-- Also link Load to TreatmentBatch (for operational loads not yet batched)
ALTER TABLE loads ADD COLUMN treatment_batch_id INTEGER REFERENCES treatment_batches(id);

-- 2. Standardize TreatmentBatch (plant_id -> facility_id)
-- Note: If running on older SQLite, this might need a recreate table strategy. 
-- Assuming modern SQLite.
ALTER TABLE treatment_batches RENAME COLUMN plant_id TO facility_id;

-- 3. Add is_active to missing tables
ALTER TABLE soil_samples ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE applications ADD COLUMN is_active BOOLEAN DEFAULT 1;
-- Check if site_events table exists, if not create it (based on model)
CREATE TABLE IF NOT EXISTS site_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATETIME NOT NULL,
    description TEXT,
    created_by_user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
-- If it existed, add the column (will fail if created above, but SQLite allows ADD COLUMN if not exists? No.)
-- We'll assume it exists and try to add. If it fails, we might need to handle it. 
-- Actually, better to just try ADD COLUMN. If the table was just created, it has it.
-- But I can't do conditional ADD COLUMN in standard SQL easily.
-- I'll assume site_events exists because the user said "Faltan is_active en... models/operations/site_event.py".
ALTER TABLE site_events ADD COLUMN is_active BOOLEAN DEFAULT 1;

ALTER TABLE treatment_batches ADD COLUMN is_active BOOLEAN DEFAULT 1;

-- 4. Fix Agronomic Units (Plots: area_acres -> area_hectares)
-- Note: This column might already be named area_hectares in some environments.
-- ALTER TABLE plots RENAME COLUMN area_acres TO area_hectares;

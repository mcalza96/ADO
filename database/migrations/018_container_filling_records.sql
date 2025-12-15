-- Migration: Create container_filling_records table
-- Date: 2025-12-04
-- Description: Tracks container filling at treatment plant with pH measurements at 0, 2, and 24 hours

-- Create container_filling_records table
CREATE TABLE IF NOT EXISTS container_filling_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id INTEGER NOT NULL,
    treatment_plant_id INTEGER NOT NULL,
    
    -- Fill completion time
    fill_end_time DATETIME NOT NULL,
    
    -- Initial measurements (required at creation)
    humidity REAL NOT NULL CHECK (humidity >= 0 AND humidity <= 100),
    ph_0h REAL NOT NULL CHECK (ph_0h >= 0 AND ph_0h <= 14),
    ph_0h_recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 2-hour pH measurement (recorded later)
    ph_2h REAL CHECK (ph_2h >= 0 AND ph_2h <= 14),
    ph_2h_recorded_at DATETIME,
    
    -- 24-hour pH measurement (recorded later)
    ph_24h REAL CHECK (ph_24h >= 0 AND ph_24h <= 14),
    ph_24h_recorded_at DATETIME,
    
    -- Status: PENDING_PH -> READY_FOR_DISPATCH -> DISPATCHED
    -- PENDING_PH: Container filled, waiting for pH measurements
    status TEXT NOT NULL DEFAULT 'PENDING_PH' CHECK (status IN ('PENDING_PH', 'READY_FOR_DISPATCH', 'DISPATCHED')),
    
    -- Reference to load when dispatched (for traceability)
    dispatched_load_id INTEGER,
    dispatched_at DATETIME,
    
    -- Which container position (1 or 2) when dispatched
    container_position INTEGER CHECK (container_position IN (1, 2)),
    
    -- Audit fields
    notes TEXT,
    created_by TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (container_id) REFERENCES containers(id) ON DELETE RESTRICT,
    FOREIGN KEY (treatment_plant_id) REFERENCES treatment_plants(id) ON DELETE RESTRICT,
    FOREIGN KEY (dispatched_load_id) REFERENCES loads(id) ON DELETE SET NULL
);

-- Index for finding active records by treatment plant
CREATE INDEX IF NOT EXISTS idx_cfr_treatment_plant_status 
ON container_filling_records(treatment_plant_id, status) WHERE is_active = 1;

-- Index for finding records by container
CREATE INDEX IF NOT EXISTS idx_cfr_container 
ON container_filling_records(container_id, status) WHERE is_active = 1;

-- Unique constraint: A container can only have one active non-dispatched record
CREATE UNIQUE INDEX IF NOT EXISTS idx_cfr_unique_active_container 
ON container_filling_records(container_id) 
WHERE status != 'DISPATCHED' AND is_active = 1;

-- Add IN_USE_TREATMENT status to containers table
-- First, we need to update the CHECK constraint
-- SQLite doesn't support ALTER CONSTRAINT, so we document this for manual update or recreation

-- Update containers status constraint to include new status
-- NOTE: In SQLite, this requires table recreation. For now, we'll handle this in application logic.
-- The new valid statuses should be: 'AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED', 'IN_USE_TREATMENT'


-- Migration: Add treatment_plant_id to pickup_requests for DS4 requests
-- Date: 2025-12-03
-- Description: Enables pickup requests from treatment plants (internal requests)
--              Makes client_id and facility_id nullable for internal requests

-- ==========================================
-- 1. Add treatment_plant_id column
-- ==========================================
ALTER TABLE pickup_requests ADD COLUMN treatment_plant_id INTEGER REFERENCES treatment_plants(id);

-- ==========================================
-- 2. Create index for treatment plant lookups
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_pickup_requests_treatment_plant ON pickup_requests(treatment_plant_id, status);

-- ==========================================
-- Note: SQLite doesn't support modifying column constraints directly.
-- The columns client_id and facility_id were created as NOT NULL.
-- To allow NULL values, we need to recreate the table.
-- However, for simplicity, we'll handle this at the application level
-- by inserting 0 or a special value for internal requests if needed.
-- 
-- In production, consider recreating the table with nullable columns:
-- 1. Create new table with correct schema
-- 2. Copy data
-- 3. Drop old table
-- 4. Rename new table
-- ==========================================

-- For now, let's check if we can make it work with the existing schema
-- by allowing client_id = NULL via a new table recreation

-- Backup and recreate with nullable columns
CREATE TABLE IF NOT EXISTS pickup_requests_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,  -- Now nullable for internal requests
    facility_id INTEGER,  -- Now nullable for internal requests
    treatment_plant_id INTEGER,  -- New: for treatment plant origin
    requested_date DATE NOT NULL,
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('BATEA', 'AMPLIROLL')),
    load_quantity INTEGER NOT NULL CHECK (load_quantity > 0),
    containers_per_load INTEGER CHECK (containers_per_load IS NULL OR (containers_per_load >= 1 AND containers_per_load <= 2)),
    notes TEXT,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PARTIALLY_SCHEDULED', 'FULLY_SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    FOREIGN KEY (treatment_plant_id) REFERENCES treatment_plants(id) ON DELETE CASCADE,
    -- Constraint: Must have either facility_id OR treatment_plant_id
    CHECK (facility_id IS NOT NULL OR treatment_plant_id IS NOT NULL)
);

-- Copy existing data
INSERT INTO pickup_requests_new (
    id, client_id, facility_id, treatment_plant_id, requested_date, 
    vehicle_type, load_quantity, containers_per_load, notes, 
    status, is_active, created_at, updated_at
)
SELECT 
    id, client_id, facility_id, NULL, requested_date,
    vehicle_type, load_quantity, containers_per_load, notes,
    status, is_active, created_at, updated_at
FROM pickup_requests;

-- Drop old table
DROP TABLE IF EXISTS pickup_requests;

-- Rename new table
ALTER TABLE pickup_requests_new RENAME TO pickup_requests;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_pickup_requests_client ON pickup_requests(client_id, status);
CREATE INDEX IF NOT EXISTS idx_pickup_requests_facility ON pickup_requests(facility_id, requested_date);
CREATE INDEX IF NOT EXISTS idx_pickup_requests_status ON pickup_requests(status, requested_date);
CREATE INDEX IF NOT EXISTS idx_pickup_requests_treatment_plant ON pickup_requests(treatment_plant_id, status);

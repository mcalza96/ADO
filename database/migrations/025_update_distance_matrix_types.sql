-- Migration: Add TREATMENT_PLANT as valid destination_type in distance_matrix
-- Date: 2025-12-05
-- Description: Allows treatment plants (own plants) as valid destinations in the distance matrix

-- SQLite doesn't support ALTER CONSTRAINT, so we need to recreate the table

-- Step 1: Create backup
CREATE TABLE IF NOT EXISTS distance_matrix_backup AS SELECT * FROM distance_matrix;

-- Step 2: Drop the old table
DROP TABLE IF EXISTS distance_matrix;

-- Step 3: Recreate table with updated CHECK constraint
CREATE TABLE distance_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_facility_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    destination_type TEXT NOT NULL CHECK (destination_type IN ('FACILITY', 'TREATMENT_PLANT', 'SITE')),
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    is_link_segment INTEGER NOT NULL DEFAULT 0 CHECK (is_link_segment IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    UNIQUE(origin_facility_id, destination_id, destination_type)
);

-- Step 4: Restore data from backup
INSERT INTO distance_matrix (
    id, 
    origin_facility_id, 
    destination_id, 
    destination_type, 
    distance_km, 
    is_link_segment, 
    created_at, 
    updated_at
)
SELECT 
    id,
    origin_facility_id,
    destination_id,
    destination_type,
    distance_km,
    is_link_segment,
    created_at,
    updated_at
FROM distance_matrix_backup;

-- Step 5: Drop backup
DROP TABLE IF EXISTS distance_matrix_backup;

-- Step 6: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_distance_matrix_origin 
ON distance_matrix(origin_facility_id);

CREATE INDEX IF NOT EXISTS idx_distance_matrix_destination 
ON distance_matrix(destination_id, destination_type);

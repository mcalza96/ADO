-- Migration: Update Load Status Check Constraint
-- Purpose: Expand allowed status values to match the granular LoadStatus enum in the application
-- Date: 2025-12-02

-- SQLite does not support ALTER COLUMN directly for CHECK constraints.
-- We must recreate the table.

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- 0. Drop broken view that depends on loads
DROP VIEW IF EXISTS view_full_traceability;

-- 1. Rename existing table
ALTER TABLE loads RENAME TO loads_old;

-- 2. Create new table with updated CHECK constraint
CREATE TABLE loads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manifest_code TEXT UNIQUE,
    
    -- Relationships
    origin_facility_id INTEGER NOT NULL,
    contractor_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    container_id INTEGER,
    destination_site_id INTEGER NOT NULL,
    destination_plot_id INTEGER NOT NULL,
    
    -- Operational Data
    material_class TEXT CHECK (material_class IN ('Class A', 'Class B')),
    gross_weight REAL,
    tare_weight REAL,
    net_weight REAL,
    
    -- Status and Timing
    status TEXT NOT NULL CHECK (status IN (
        'CREATED', 
        'REQUESTED', 
        'ASSIGNED', 
        'ACCEPTED', 
        'EN_ROUTE_PICKUP', 
        'AT_PICKUP', 
        'EN_ROUTE_DESTINATION', 
        'AT_DESTINATION', 
        'IN_DISPOSAL', 
        'COMPLETED', 
        'CANCELLED'
    )) DEFAULT 'CREATED',
    
    dispatch_time DATETIME,
    arrival_time DATETIME,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    attributes TEXT DEFAULT '{}',
    
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
    FOREIGN KEY (contractor_id) REFERENCES contractors(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (container_id) REFERENCES containers(id),
    FOREIGN KEY (destination_site_id) REFERENCES sites(id),
    FOREIGN KEY (destination_plot_id) REFERENCES plots(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- 3. Copy data from old table
INSERT INTO loads (
    id, manifest_code, origin_facility_id, contractor_id, vehicle_id, driver_id, 
    container_id, destination_site_id, destination_plot_id, material_class, 
    gross_weight, tare_weight, net_weight, status, dispatch_time, arrival_time, 
    created_at, updated_at, created_by_user_id, attributes
)
SELECT 
    id, manifest_code, origin_facility_id, contractor_id, vehicle_id, driver_id, 
    container_id, destination_site_id, destination_plot_id, material_class, 
    gross_weight, tare_weight, net_weight, status, dispatch_time, arrival_time, 
    created_at, updated_at, created_by_user_id, attributes
FROM loads_old;

-- 4. Drop old table
DROP TABLE loads_old;

COMMIT;

PRAGMA foreign_keys=on;

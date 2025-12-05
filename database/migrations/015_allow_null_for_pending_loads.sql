-- Migration 015: Allow NULL values for fields not known at request time
-- When a client creates a pickup request, these fields are assigned later by the planner
-- SQLite doesn't support ALTER COLUMN, so we need to recreate the table

-- Step 1: Create new table with nullable contractor_id, vehicle_id, driver_id, destination columns
CREATE TABLE IF NOT EXISTS loads_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manifest_code TEXT UNIQUE,
    
    -- Relationships (some nullable for REQUESTED status)
    origin_facility_id INTEGER NOT NULL,
    contractor_id INTEGER,  -- NULL when REQUESTED, assigned by planner
    vehicle_id INTEGER,     -- NULL when REQUESTED, assigned by planner
    driver_id INTEGER,      -- NULL when REQUESTED, assigned by planner
    container_id INTEGER,
    destination_site_id INTEGER,     -- NULL when REQUESTED, assigned by planner
    destination_plot_id INTEGER,     -- NULL when REQUESTED, assigned by planner
    batch_id INTEGER,
    treatment_batch_id INTEGER,
    origin_treatment_plant_id INTEGER,
    destination_treatment_plant_id INTEGER,
    
    -- Pickup Request fields
    pickup_request_id INTEGER,
    vehicle_type_requested TEXT,
    container_quantity INTEGER,
    
    -- Operational Data
    material_class TEXT CHECK (material_class IN ('Class A', 'Class B')),
    gross_weight REAL,
    tare_weight REAL,
    net_weight REAL,
    weight_gross_reception REAL,
    reception_observations TEXT,
    quality_ph REAL,
    quality_humidity REAL,
    
    -- Document Numbers
    ticket_number TEXT,
    guide_number TEXT,
    
    -- Status and Timing
    status TEXT NOT NULL CHECK (status IN ('REQUESTED', 'CREATED', 'SCHEDULED', 'IN_TRANSIT', 'ARRIVED', 'COMPLETED', 'CANCELLED')) DEFAULT 'CREATED',
    requested_date DATE,
    scheduled_date DATE,
    dispatch_time DATETIME,
    arrival_time DATETIME,
    disposal_time DATETIME,
    
    -- Flexible attributes (JSON)
    attributes TEXT DEFAULT '{}',
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
    FOREIGN KEY (contractor_id) REFERENCES contractors(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (container_id) REFERENCES containers(id),
    FOREIGN KEY (destination_site_id) REFERENCES disposal_sites(id),
    FOREIGN KEY (destination_plot_id) REFERENCES plots(id),
    FOREIGN KEY (pickup_request_id) REFERENCES pickup_requests(id)
);

-- Step 2: Copy existing data
INSERT INTO loads_new (
    id, manifest_code, origin_facility_id, contractor_id, vehicle_id, driver_id,
    container_id, destination_site_id, destination_plot_id, batch_id, treatment_batch_id,
    origin_treatment_plant_id, destination_treatment_plant_id,
    pickup_request_id, vehicle_type_requested, container_quantity,
    material_class, gross_weight, tare_weight, net_weight, weight_gross_reception,
    reception_observations, quality_ph, quality_humidity,
    ticket_number, guide_number,
    status, requested_date, scheduled_date, dispatch_time, arrival_time, disposal_time,
    attributes, created_at, updated_at, created_by_user_id
)
SELECT 
    id, manifest_code, origin_facility_id, contractor_id, vehicle_id, driver_id,
    container_id, destination_site_id, destination_plot_id, batch_id, treatment_batch_id,
    origin_treatment_plant_id, destination_treatment_plant_id,
    pickup_request_id, vehicle_type_requested, container_quantity,
    material_class, gross_weight, tare_weight, net_weight, weight_gross_reception,
    reception_observations, quality_ph, quality_humidity,
    ticket_number, guide_number,
    status, requested_date, scheduled_date, dispatch_time, arrival_time, disposal_time,
    COALESCE(attributes, '{}'), created_at, updated_at, created_by_user_id
FROM loads;

-- Step 3: Drop old table and rename new one
DROP TABLE loads;
ALTER TABLE loads_new RENAME TO loads;

-- Step 4: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_loads_status ON loads(status);
CREATE INDEX IF NOT EXISTS idx_loads_origin ON loads(origin_facility_id);
CREATE INDEX IF NOT EXISTS idx_loads_contractor ON loads(contractor_id);
CREATE INDEX IF NOT EXISTS idx_loads_pickup_request ON loads(pickup_request_id);

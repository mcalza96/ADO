-- Migration 029: Create client_plant_tariffs table
-- Purpose: Store versioned tariffs per client facility for different service types
-- Service types: TTE (Transport), TTO (Treatment), DISP (Disposal), 
--                Relleno_TTE (Landfill from treatment), Relleno_DISP (Landfill direct disposal)

CREATE TABLE IF NOT EXISTS client_plant_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Client and origin facility (plant)
    client_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    
    -- Tariff rates in UF/ton for each service type
    rate_tte_uf REAL CHECK (rate_tte_uf IS NULL OR rate_tte_uf >= 0),
    rate_tto_uf REAL CHECK (rate_tto_uf IS NULL OR rate_tto_uf >= 0),
    rate_disp_uf REAL CHECK (rate_disp_uf IS NULL OR rate_disp_uf >= 0),
    rate_landfill_tte_uf REAL CHECK (rate_landfill_tte_uf IS NULL OR rate_landfill_tte_uf >= 0),
    rate_landfill_disp_uf REAL CHECK (rate_landfill_disp_uf IS NULL OR rate_landfill_disp_uf >= 0),
    
    -- Temporal validity for versioning
    valid_from DATE NOT NULL,
    valid_to DATE,  -- NULL means currently active
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    
    -- Foreign keys
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    
    -- Ensure facility belongs to client
    CHECK (
        EXISTS (
            SELECT 1 FROM facilities f 
            WHERE f.id = facility_id AND f.client_id = client_id
        )
    ),
    
    -- Prevent overlapping validity periods for same client-facility combination
    UNIQUE (client_id, facility_id, valid_from)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_client_plant_tariffs_client 
    ON client_plant_tariffs(client_id);

CREATE INDEX IF NOT EXISTS idx_client_plant_tariffs_facility 
    ON client_plant_tariffs(facility_id);

CREATE INDEX IF NOT EXISTS idx_client_plant_tariffs_validity 
    ON client_plant_tariffs(client_id, facility_id, valid_from, valid_to);

-- Partial index for active tariffs (most common query)
CREATE INDEX IF NOT EXISTS idx_client_plant_tariffs_active 
    ON client_plant_tariffs(client_id, facility_id) 
    WHERE valid_to IS NULL;

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_client_plant_tariffs_timestamp 
    AFTER UPDATE ON client_plant_tariffs
    FOR EACH ROW
BEGIN
    UPDATE client_plant_tariffs 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Comments for documentation
-- TTE (Transporte): Transport service tariff
-- TTO (Tratamiento): Treatment service tariff  
-- DISP (Disposición): Direct disposal tariff
-- Relleno_TTE: Sanitary landfill tariff when coming from treatment plant
-- Relleno_DISP: Sanitary landfill tariff for direct disposal

-- Migration 030: Create sanitary_landfills table
-- Purpose: Add sanitary landfills as a third destination type (besides treatment plants and disposal sites)
-- Workflow: Driver confirms dispatch -> travels -> confirms arrival -> cycle ends (no additional reception needed)

CREATE TABLE IF NOT EXISTS sanitary_landfills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Basic information
    name TEXT NOT NULL UNIQUE,
    code TEXT UNIQUE,
    
    -- Location
    address TEXT,
    region TEXT,
    commune TEXT,
    latitude REAL,
    longitude REAL,
    
    -- Contact information
    contact_name TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    
    -- Operational information
    operating_company TEXT,
    environmental_permit TEXT,
    max_daily_capacity_tons REAL CHECK (max_daily_capacity_tons IS NULL OR max_daily_capacity_tons > 0),
    accepts_waste_types TEXT,  -- JSON array of accepted waste types
    
    -- Status
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT,
    
    -- Notes
    notes TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sanitary_landfills_name 
    ON sanitary_landfills(name);

CREATE INDEX IF NOT EXISTS idx_sanitary_landfills_active 
    ON sanitary_landfills(is_active) 
    WHERE is_active = 1;

CREATE INDEX IF NOT EXISTS idx_sanitary_landfills_region 
    ON sanitary_landfills(region);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_sanitary_landfills_timestamp 
    AFTER UPDATE ON sanitary_landfills
    FOR EACH ROW
BEGIN
    UPDATE sanitary_landfills 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Insert sample sanitary landfills for testing
INSERT OR IGNORE INTO sanitary_landfills (
    name, 
    code, 
    address, 
    region, 
    commune, 
    contact_name,
    operating_company,
    is_active
) VALUES 
    (
        'Relleno Sanitario KDM Loma Los Colorados',
        'RS_KDM_LLC',
        'Camino a Til Til km 32',
        'Región Metropolitana',
        'Til Til',
        'Contacto KDM',
        'KDM Empresa de Servicios',
        1
    ),
    (
        'Relleno Sanitario Santa Marta',
        'RS_SANTA_MARTA',
        'Ruta 68, km 60',
        'Región de Valparaíso',
        'Talagante',
        'Contacto Santa Marta',
        'Gestión y Servicios',
        1
    );

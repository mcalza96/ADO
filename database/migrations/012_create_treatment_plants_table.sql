-- Migration: Create treatment_plants table
-- Date: 2025-12-03
-- Description: Separates Treatment Plants (own processing plants) from Facilities (client origin plants)

-- Create treatment_plants table for own processing plants
CREATE TABLE IF NOT EXISTS treatment_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    latitude REAL,
    longitude REAL,
    authorization_resolution TEXT,  -- Resolución de autorización sanitaria
    state_permit_number TEXT,       -- Número de permiso estatal
    allowed_vehicle_types TEXT,     -- CSV: "BATEA,AMPLIROLL"
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for active plants
CREATE INDEX IF NOT EXISTS idx_treatment_plants_active ON treatment_plants(is_active);

-- Migration: Sprint 3 - Add Compliance Fields
-- Date: 2025-11-29
-- Description: Add nutrient analysis and heavy metals fields to batches table
--              Add nitrogen limit field to plots table
--              Create nitrogen_applications table for tracking historical N applications

-- 1. Add fields to batches table
ALTER TABLE batches ADD COLUMN nitrate_no3 REAL;
ALTER TABLE batches ADD COLUMN ammonium_nh4 REAL;
ALTER TABLE batches ADD COLUMN tkn REAL;
ALTER TABLE batches ADD COLUMN percent_solids REAL;
ALTER TABLE batches ADD COLUMN heavy_metals_json TEXT;

-- 2. Add nitrogen limit to plots table
ALTER TABLE plots ADD COLUMN nitrogen_limit_kg_per_ha REAL;

-- 3. Create nitrogen_applications table
CREATE TABLE IF NOT EXISTS nitrogen_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    load_id INTEGER,
    application_date DATE NOT NULL,
    nitrogen_applied_kg REAL NOT NULL,
    area_ha REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id),
    FOREIGN KEY (load_id) REFERENCES loads(id)
);

-- 4. Create index for efficient year queries
CREATE INDEX IF NOT EXISTS idx_nitrogen_apps_site_date 
ON nitrogen_applications(site_id, application_date);

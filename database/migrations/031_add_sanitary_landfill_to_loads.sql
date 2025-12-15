-- Migration 031: Add destination_sanitary_landfill_id to loads table
-- Purpose: Support sanitary landfills as a third destination type for waste disposal

-- Add new column to loads table
ALTER TABLE loads ADD COLUMN destination_sanitary_landfill_id INTEGER 
    REFERENCES sanitary_landfills(id) ON DELETE SET NULL;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_loads_destination_sanitary_landfill 
    ON loads(destination_sanitary_landfill_id);

-- Add constraint to ensure only one destination type is set
-- Note: SQLite doesn't support CHECK with subqueries, so this is enforced at application level
-- Application must ensure that only ONE of these is non-NULL:
-- - destination_site_id
-- - destination_treatment_plant_id  
-- - destination_sanitary_landfill_id

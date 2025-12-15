-- Migration: Add arrival_ph field to loads table
-- Date: 2025-12-04
-- Description: Adds arrival_ph column to store pH measurement when load arrives
--              at treatment plant (separate from dispatch pH)

-- Add arrival_ph column for pH measured at arrival to treatment plant
ALTER TABLE loads 
ADD COLUMN arrival_ph REAL CHECK (arrival_ph >= 0 AND arrival_ph <= 14);

-- Migration Notes:
-- - This field is specifically for loads arriving at treatment plants from client facilities
-- - quality_ph remains the pH at dispatch (origin)
-- - arrival_ph is the pH verified at arrival (destination)
-- - This enables full traceability: pH at origin vs pH at arrival


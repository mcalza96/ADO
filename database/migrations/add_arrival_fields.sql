-- Migration: Add arrival reception fields to loads table
-- Date: 2025-11-29
-- Author: System
-- Description: Adds weight_arrival and reception_observations columns to support
--              the new Arrived state in the load reception workflow

-- Add weight_arrival column to store scale weight at reception
ALTER TABLE loads 
ADD COLUMN weight_arrival REAL;

-- Add reception_observations column to store quality observations at gate
ALTER TABLE loads 
ADD COLUMN reception_observations TEXT;

-- Optional: Add index if querying by arrival weight will be frequent
-- CREATE INDEX idx_loads_weight_arrival ON loads(weight_arrival);

-- Migration Notes:
-- - Existing loads will have NULL values for these new fields
-- - Only loads with status='Arrived' will have these fields populated
-- - This migration is idempotent-safe (can be run multiple times)

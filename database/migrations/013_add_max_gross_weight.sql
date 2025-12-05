-- Migration: Add max_gross_weight to vehicles
-- Date: 2025-12-03
-- Description: Adds max_gross_weight column and calculates from existing data
--              capacity_wet_tons becomes a calculated property in the entity

-- Add max_gross_weight column (Peso Bruto Vehicular máximo en kg)
ALTER TABLE vehicles ADD COLUMN max_gross_weight REAL;

-- Migrate existing data: max_gross_weight = tare_weight + (capacity_wet_tons * 1000)
-- capacity_wet_tons was in tons, we store weights in kg
UPDATE vehicles 
SET max_gross_weight = tare_weight + (capacity_wet_tons * 1000)
WHERE max_gross_weight IS NULL;

-- Set default for any remaining nulls (30 tons gross weight)
UPDATE vehicles 
SET max_gross_weight = 30000 
WHERE max_gross_weight IS NULL OR max_gross_weight = 0;

-- Note: capacity_wet_tons column remains for backward compatibility
-- but the entity now calculates it as: (max_gross_weight - tare_weight) / 1000

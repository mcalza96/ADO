-- Migration: Add vehicle type columns
-- Date: 2025-01-XX
-- Description: Adds type column to vehicles table and allowed_vehicle_types to facilities

-- Add type column to vehicles with default value BATEA
ALTER TABLE vehicles ADD COLUMN type TEXT DEFAULT 'BATEA';

-- Update existing vehicles to have BATEA type if null
UPDATE vehicles SET type = 'BATEA' WHERE type IS NULL;

-- Add allowed_vehicle_types to facilities (CSV format: "BATEA,AMPLIROLL")
ALTER TABLE facilities ADD COLUMN allowed_vehicle_types TEXT;

-- By default, allow all vehicle types for existing facilities
UPDATE facilities SET allowed_vehicle_types = 'BATEA,AMPLIROLL' WHERE allowed_vehicle_types IS NULL;

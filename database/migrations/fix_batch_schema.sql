-- Fix: Add missing current_tonnage column to batches
ALTER TABLE batches ADD COLUMN current_tonnage REAL;

-- Initialize current_tonnage with initial_tonnage for existing records
UPDATE batches SET current_tonnage = initial_tonnage WHERE current_tonnage IS NULL;

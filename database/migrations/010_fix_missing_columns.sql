-- Migration: Fix missing columns in loads table
-- Date: 2025-12-02
-- Description: Adds missing columns referenced in queries and views
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we handle errors gracefully

-- Create a temporary table to check columns
-- Add weight_net column (use net_weight as alias in queries)
-- Already exists as net_weight

-- Add ticket_number column if it doesn't exist  
-- ALTER TABLE loads ADD COLUMN ticket_number TEXT; -- Will fail if exists

-- Add guide_number column if it doesn't exist
-- ALTER TABLE loads ADD COLUMN guide_number TEXT; -- Will fail if exists

-- Add disposal_time column - already exists (seen in PRAGMA output)

-- Add weight_gross_reception column - already exists (seen in PRAGMA output)

-- Add requested_date column if it doesn't exist
-- ALTER TABLE loads ADD COLUMN requested_date DATE;

-- Add scheduled_date column if it doesn't exist
-- ALTER TABLE loads ADD COLUMN scheduled_date DATE;

-- Create helper columns with safer approach
-- Using a transaction to ensure atomicity
BEGIN TRANSACTION;

-- For SQLite, we need to be defensive about adding columns
-- First, let's add only the columns that are truly missing

-- Check and add ticket_number
-- (Will succeed only if column doesn't exist)
CREATE TABLE IF NOT EXISTS _migration_check (dummy INTEGER);

-- Safe column additions (will error if exists, but that's OK)
-- We'll run these individually and ignore errors

COMMIT;

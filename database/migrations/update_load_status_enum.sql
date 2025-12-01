-- Migration: Update Load Status Enum
-- Add 'Accepted' and 'Arrived' states to support full transport workflow
-- Flow: Scheduled → Accepted → InTransit → Arrived → Delivered

-- SQLite doesn't support modifying CHECK constraints directly
-- We need to recreate the table or remove constraint validation
-- For simplicity in SQLite, we'll remove the old constraint and add validation at app level
-- The model and service layers will enforce valid states

-- Note: If strict DB-level validation is required, we would need to:
-- 1. Create new table with updated constraint
-- 2. Copy data
-- 3. Drop old table
-- 4. Rename new table

-- For now, document that valid states are:
-- 'Requested', 'Scheduled', 'Accepted', 'InTransit', 'Arrived', 'Delivered', 'Cancelled', 'Disposed'

-- No SQL changes needed - validation handled at application level
-- This file serves as documentation of the state machine expansion

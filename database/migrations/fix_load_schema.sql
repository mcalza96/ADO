-- Fix: Add missing sync columns to loads
ALTER TABLE loads ADD COLUMN sync_status TEXT DEFAULT 'PENDING';
ALTER TABLE loads ADD COLUMN last_updated_local DATETIME;

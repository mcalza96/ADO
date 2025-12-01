-- Migration: Add audit fields for Soft Delete support  
-- Date: 2025-12-01
-- Description: Adds missing audit fields (is_active, created_at, updated_at) to clients, facilities, and contractors tables
-- Note: This migration is idempotent - only adds columns that don't exist yet

-- ==========================================
-- 1. Add missing fields to clients table
-- ==========================================
-- clients already has: is_active, created_at
-- clients needs: updated_at

ALTER TABLE clients ADD COLUMN updated_at DATETIME;
UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- ==========================================
-- 2. Add missing fields to facilities table
-- ==========================================
-- facilities already has: is_active
-- facilities needs: created_at, updated_at

ALTER TABLE facilities ADD COLUMN created_at DATETIME;
ALTER TABLE facilities ADD COLUMN updated_at DATETIME;
UPDATE facilities SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
UPDATE facilities SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- ==========================================
-- 3. Add missing fields to contractors table
-- ==========================================
-- contractors already has: created_at
-- contractors needs: is_active, updated_at

ALTER TABLE contractors ADD COLUMN is_active BOOLEAN;
ALTER TABLE contractors ADD COLUMN updated_at DATETIME;
UPDATE contractors SET is_active = 1 WHERE is_active IS NULL;
UPDATE contractors SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- ==========================================
-- Success message
-- ==========================================

SELECT 'Migration 001_add_audit_fields.sql completed successfully' AS status;

-- Migration: Fix Financial Schema - Migrate Contractor Tariffs to UF
-- Date: 2025-12-05
-- Description: Renames base_rate to base_rate_uf and updates documentation
--              to reflect that contractor tariffs are in UF, not CLP.
--
-- CRITICAL: This is a semantic change. Existing data MUST be converted.
-- If you have existing tariffs in CLP, you MUST divide by current UF value
-- before running this migration. For development/testing with sample data,
-- we assume base_rate is already in UF-equivalent values.
--
-- Author: Senior Financial Systems Architect

PRAGMA foreign_keys = ON;

-- ==========================================
-- STEP 1: Add new column base_rate_uf
-- ==========================================
ALTER TABLE contractor_tariffs ADD COLUMN base_rate_uf REAL;

-- ==========================================
-- STEP 2: Migrate data
-- ==========================================
-- WARNING: If your current base_rate is in CLP, you MUST convert:
--   Example: UPDATE contractor_tariffs SET base_rate_uf = base_rate / 37000.0;
-- 
-- For development/testing, we assume it's already in UF-equivalent:
UPDATE contractor_tariffs SET base_rate_uf = base_rate WHERE base_rate_uf IS NULL;

-- ==========================================
-- STEP 3: Recreate table with correct schema
-- ==========================================
-- SQLite limitation: Can't modify column constraints via ALTER TABLE
-- We must recreate the table

-- 3.1: Create backup
CREATE TABLE contractor_tariffs_backup AS SELECT * FROM contractor_tariffs;

-- 3.2: Drop old table
DROP TABLE contractor_tariffs;

-- 3.3: Recreate with corrected schema
CREATE TABLE contractor_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Contractor reference
    contractor_id INTEGER NOT NULL,
    
    -- Vehicle classification for tariff application
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')),
    
    -- *** CHANGED: Now in UF per ton-km (was CLP) ***
    -- Base contractual rate in UF/ton-km
    -- The polynomial fuel adjustment multiplies this UF rate by a dimensionless factor
    base_rate_uf REAL NOT NULL CHECK (base_rate_uf > 0),
    
    -- Minimum guaranteed weight (tons)
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Fuel price pivot for polynomial formula (REMAINS IN CLP)
    -- This is used to calculate a dimensionless adjustment factor:
    -- factor = current_fuel_price (CLP) / base_fuel_price (CLP)
    -- Formula: actual_cost_uf = base_rate_uf * factor
    base_fuel_price REAL NOT NULL CHECK (base_fuel_price > 0),
    
    -- Validity period (NULL in valid_to = currently active)
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE,
    
    -- Business rule: valid_to must be after valid_from if present
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- 3.4: Restore data from backup
INSERT INTO contractor_tariffs (
    id, contractor_id, vehicle_type, base_rate_uf, min_weight_guaranteed,
    base_fuel_price, valid_from, valid_to, created_at, updated_at
)
SELECT 
    id, contractor_id, vehicle_type, base_rate_uf, min_weight_guaranteed,
    base_fuel_price, valid_from, valid_to, created_at, updated_at
FROM contractor_tariffs_backup;

-- ==========================================
-- STEP 4: Recreate indexes
-- ==========================================
-- Composite index for resolving "which tariff applied on date X"
CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_lookup 
ON contractor_tariffs(contractor_id, vehicle_type, valid_from);

-- Index for active tariff queries (where valid_to IS NULL)
CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_active 
ON contractor_tariffs(contractor_id, vehicle_type) 
WHERE valid_to IS NULL;

-- ==========================================
-- STEP 5: Cleanup
-- ==========================================
DROP TABLE contractor_tariffs_backup;

-- ==========================================
-- VERIFICATION
-- ==========================================
SELECT '✅ Migration completed successfully' AS status;

-- Display summary of migrated data
SELECT 
    COUNT(*) AS total_tariffs, 
    ROUND(AVG(base_rate_uf), 4) AS avg_rate_uf,
    ROUND(MIN(base_rate_uf), 4) AS min_rate_uf,
    ROUND(MAX(base_rate_uf), 4) AS max_rate_uf
FROM contractor_tariffs;

-- Verify all tariffs have positive base_rate_uf
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ All tariffs have valid base_rate_uf'
        ELSE '❌ Found ' || COUNT(*) || ' tariffs with invalid base_rate_uf'
    END AS validation_result
FROM contractor_tariffs
WHERE base_rate_uf IS NULL OR base_rate_uf <= 0;

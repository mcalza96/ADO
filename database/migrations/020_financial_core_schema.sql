-- Migration: Financial Core Schema - Billing and Payments Foundation
-- Date: 2025-12-05
-- Description: Implements the financial module for polynomial tariffs and logistics costing
--              Creates: economic_indicators, distance_matrix, contractor_tariffs, client_tariffs
--              Extends: loads table with financial tracking fields
--
-- CRITICAL: This is the foundation for billing. Data integrity is MAXIMUM priority.
-- Standard: Zero-Bug Tolerance
-- Author: Principal Database Architect

-- Enable Foreign Keys enforcement
PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. ECONOMIC INDICATORS TABLE
-- Purpose: Immutable financial truth for historical calculations
-- ==========================================
CREATE TABLE IF NOT EXISTS economic_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Period identifier: 'YYYY-MM' format (e.g., '2025-11')
    period_key TEXT NOT NULL UNIQUE,
    
    -- Operational cycle: from day 19 to day 18 of next month
    cycle_start_date DATE NOT NULL,
    cycle_end_date DATE NOT NULL,
    
    -- Financial reference values (immutable after cycle closure)
    uf_value REAL NOT NULL CHECK (uf_value > 0),
    fuel_price REAL NOT NULL CHECK (fuel_price > 0),
    
    -- Cycle status: OPEN = editable, CLOSED = locked
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Business rule: End date must be after start date
    CHECK (cycle_end_date > cycle_start_date)
);

-- Index for fast period lookups in billing queries
CREATE INDEX IF NOT EXISTS idx_economic_indicators_period 
ON economic_indicators(period_key);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_economic_indicators_dates 
ON economic_indicators(cycle_start_date, cycle_end_date);

-- ==========================================
-- 2. DISTANCE MATRIX TABLE
-- Purpose: Define the logistics graph (allowed routes and distances)
-- ==========================================
CREATE TABLE IF NOT EXISTS distance_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Origin is always a facility (treatment plant)
    origin_facility_id INTEGER NOT NULL,
    
    -- Destination is polymorphic: can be FACILITY or SITE
    -- This enables mixed routes: Plant->Site (direct) or Plant->Plant->Site (relay)
    destination_node_id INTEGER NOT NULL,
    destination_type TEXT NOT NULL CHECK (destination_type IN ('FACILITY', 'SITE')),
    
    -- Distance in kilometers (must be positive)
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    
    -- Is this a relay segment? (A->B in a multi-hop trip A->B->C)
    is_segment BOOLEAN DEFAULT 0,
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    
    -- Business rule: Each route can only be defined once
    UNIQUE(origin_facility_id, destination_node_id, destination_type)
);

-- Index for route lookups from origin
CREATE INDEX IF NOT EXISTS idx_distance_matrix_origin 
ON distance_matrix(origin_facility_id);

-- Composite index for mixed destination queries
CREATE INDEX IF NOT EXISTS idx_distance_matrix_origin_type 
ON distance_matrix(origin_facility_id, destination_type);

-- ==========================================
-- 3. CONTRACTOR TARIFFS TABLE
-- Purpose: Cost basis for third-party payments with fuel indexing
-- ==========================================
CREATE TABLE IF NOT EXISTS contractor_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Contractor reference
    contractor_id INTEGER NOT NULL,
    
    -- Vehicle classification for tariff application
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')),
    
    -- Base contractual rate (CLP per ton-km or similar)
    base_rate REAL NOT NULL CHECK (base_rate > 0),
    
    -- Minimum guaranteed weight (tons)
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Fuel price pivot for polynomial formula
    -- Formula: actual_cost = base_rate * (current_fuel_price / base_fuel_price)
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

-- Composite index for resolving "which tariff applied on date X"
CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_lookup 
ON contractor_tariffs(contractor_id, vehicle_type, valid_from);

-- Index for active tariff queries (where valid_to IS NULL)
CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_active 
ON contractor_tariffs(contractor_id, vehicle_type) 
WHERE valid_to IS NULL;

-- ==========================================
-- 4. CLIENT TARIFFS TABLE
-- Purpose: Revenue side - client billing rates in UF
-- ==========================================
CREATE TABLE IF NOT EXISTS client_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Client reference
    client_id INTEGER NOT NULL,
    
    -- Billing concept classification
    concept TEXT NOT NULL CHECK (concept IN ('TRANSPORTE', 'TRATAMIENTO', 'DISPOSICION')),
    
    -- Rate in UF (unidad de fomento - Chilean inflation-indexed unit)
    rate_uf REAL NOT NULL CHECK (rate_uf > 0),
    
    -- Minimum guaranteed weight (tons)
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Validity period
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Business rule: valid_to must be after valid_from if present
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- Composite index for active tariff lookups
CREATE INDEX IF NOT EXISTS idx_client_tariffs_lookup 
ON client_tariffs(client_id, concept, valid_from);

-- Index for active tariff queries
CREATE INDEX IF NOT EXISTS idx_client_tariffs_active 
ON client_tariffs(client_id, concept) 
WHERE valid_to IS NULL;

-- ==========================================
-- 5. EXTEND LOADS TABLE
-- Purpose: Inject financial logic into operational table
-- ==========================================

-- Add trip_id for grouping loads in relay/multi-hop scenarios
-- Example: Plant A -> Plant B (segment 1), Plant B -> Site (segment 2)
-- Both loads share the same trip_id
ALTER TABLE loads ADD COLUMN trip_id TEXT;

-- Financial status workflow: PENDING -> CALCULATED -> APPROVED -> BILLED
-- NOTE: SQLite limitation - cannot add CHECK constraint via ALTER TABLE
-- VALIDATION MUST BE ENFORCED IN APPLICATION LAYER
-- Valid values: 'PENDING', 'CALCULATED', 'APPROVED', 'BILLED'
ALTER TABLE loads ADD COLUMN financial_status TEXT DEFAULT 'PENDING';

-- Segment classification for trip accounting
-- NOTE: SQLite limitation - cannot add CHECK constraint via ALTER TABLE
-- VALIDATION MUST BE ENFORCED IN APPLICATION LAYER
-- Valid values: 'DIRECT', 'PICKUP_SEGMENT', 'MAIN_HAUL'
ALTER TABLE loads ADD COLUMN segment_type TEXT DEFAULT 'DIRECT';

-- Index for trip grouping queries
CREATE INDEX IF NOT EXISTS idx_loads_trip_id 
ON loads(trip_id) 
WHERE trip_id IS NOT NULL;

-- Index for financial status queries
CREATE INDEX IF NOT EXISTS idx_loads_financial_status 
ON loads(financial_status);

-- Composite index for billing queries (status + period)
CREATE INDEX IF NOT EXISTS idx_loads_billing 
ON loads(financial_status, scheduled_date);

-- ==========================================
-- MIGRATION NOTES
-- ==========================================
-- 1. All monetary constraints use CHECK (value > 0) to prevent negative amounts
-- 2. Date ranges use CHECK (end > start) to prevent invalid periods
-- 3. Enum constraints use CHECK (column IN (...)) for data integrity at DB level
-- 4. Indexes created on high-cardinality columns and common query patterns
-- 5. Foreign keys use ON DELETE CASCADE for master data, preserving referential integrity
-- 6. fields added to loads cannot have CHECK constraints due to SQLite limitations
--    Application layer MUST validate: financial_status, segment_type
-- 7. Historical tariffs are immutable - no soft delete (is_active) by design
-- 8. period_key format is enforced by application, not DB (SQLite regex limitation)
--
-- VERIFICATION CHECKLIST:
-- [ ] Run PRAGMA foreign_key_check; to verify FK integrity
-- [ ] Insert test data for each table
-- [ ] Verify all CHECK constraints by attempting invalid inserts
-- [ ] Run EXPLAIN QUERY PLAN on typical billing queries
-- [ ] Confirm indexes are used in query plans

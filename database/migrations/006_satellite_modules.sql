-- ============================================================================
-- Migration 006: Satellite Modules (Maintenance, Compliance, Finance)
-- ============================================================================
-- Description: 
--   Creates tables for the satellite domains that listen to operational events.
--   1. Maintenance: Plans and Orders
--   2. Compliance: Regulatory Documents (immutable snapshots)
--   3. Finance: Rate Sheets and Cost Records
--
-- Date: 2025-12-02
-- Phase: 3 - Satellite Modules
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. MAINTENANCE DOMAIN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS maintenance_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    maintenance_type TEXT NOT NULL, -- e.g., "Oil Change"
    frequency_value REAL NOT NULL, -- e.g., 10000
    strategy TEXT NOT NULL, -- 'BY_KM' or 'BY_HOURS'
    
    last_service_at_meter REAL DEFAULT 0.0,
    last_service_date DATETIME,
    
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    
    FOREIGN KEY (asset_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS maintenance_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    
    status TEXT DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED
    due_at_meter REAL NOT NULL,
    
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    notes TEXT,
    
    FOREIGN KEY (plan_id) REFERENCES maintenance_plans(id),
    FOREIGN KEY (asset_id) REFERENCES vehicles(id)
);

-- ----------------------------------------------------------------------------
-- 2. COMPLIANCE DOMAIN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS regulatory_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL, -- 'CERTIFICADO_DISPOSICION', 'GUIA_DESPACHO'
    related_load_id INTEGER NOT NULL,
    
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    pdf_url TEXT,
    
    -- Snapshot of load data at generation time (JSON)
    -- Critical for legal immutability
    snapshot_data TEXT, 
    
    FOREIGN KEY (related_load_id) REFERENCES loads(id)
);

-- ----------------------------------------------------------------------------
-- 3. FINANCE DOMAIN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS rate_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER, -- Optional, NULL means default rate
    activity_type TEXT NOT NULL, -- 'TRANSPORTE', 'DISPOSICION', 'MAQUINARIA'
    
    unit_price REAL NOT NULL,
    unit_type TEXT NOT NULL, -- 'POR_KM', 'POR_TON', 'POR_HORA'
    
    currency TEXT DEFAULT 'CLP',
    valid_from DATETIME DEFAULT CURRENT_TIMESTAMP,
    valid_to DATETIME,
    
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    related_entity_id INTEGER NOT NULL, -- load_id or machine_log_id
    related_entity_type TEXT NOT NULL, -- 'LOAD' or 'MACHINE_LOG'
    
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'CLP',
    
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit: which rate was used
    rate_sheet_id INTEGER,
    
    FOREIGN KEY (rate_sheet_id) REFERENCES rate_sheets(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_maint_plans_asset ON maintenance_plans(asset_id);
CREATE INDEX IF NOT EXISTS idx_maint_orders_status ON maintenance_orders(status);
CREATE INDEX IF NOT EXISTS idx_reg_docs_load ON regulatory_documents(related_load_id);
CREATE INDEX IF NOT EXISTS idx_cost_records_entity ON cost_records(related_entity_id, related_entity_type);

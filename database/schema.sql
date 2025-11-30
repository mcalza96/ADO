-- Biosolids Management ERP - MVP Database Schema
-- Database: SQLite
-- Date: 2025-11-27

-- Enable Foreign Keys enforcement
PRAGMA foreign_keys = ON;

-- ==========================================
-- General Masters Module
-- ==========================================

-- Users table: System users with roles
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, -- Store hashed passwords
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Planificador', 'Chofer', 'Operador')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Clients table: Sanitary companies (Owners of the sludge)
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rut TEXT UNIQUE, -- Tax ID
    contact_name TEXT,
    contact_email TEXT,
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- Transport Module (Logistics)
-- ==========================================

-- Contractors table: Transport companies
CREATE TABLE IF NOT EXISTS contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rut TEXT UNIQUE,
    contact_name TEXT,
    phone TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drivers table: Associated with a contractor
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rut TEXT UNIQUE,
    license_number TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Vehicles table: Trucks and trailers
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    brand TEXT,
    model TEXT,
    license_plate TEXT NOT NULL UNIQUE,
    max_capacity REAL NOT NULL, -- In Kg
    tare_weight REAL NOT NULL, -- In Kg
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- ==========================================
-- Treatment Module (Origin)
-- ==========================================

-- Facilities table: Treatment Plants (WTP)
CREATE TABLE IF NOT EXISTS facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    latitude REAL,
    longitude REAL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

-- Batches table: Production lots of biosolids
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL,
    batch_code TEXT NOT NULL UNIQUE, -- e.g., 'LOTE-2023-10-01-A'
    production_date DATE NOT NULL,
    initial_tonnage REAL,
    current_tonnage REAL,
    class_type TEXT CHECK (class_type IN ('A', 'B', 'NoClass')), -- Biosolid Classification
    status TEXT DEFAULT 'Available', -- Available, Depleted, Quarantined
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
);

-- Lab Results table: Analysis for batches
CREATE TABLE IF NOT EXISTS lab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    analysis_date DATE NOT NULL,
    parameter_name TEXT NOT NULL, -- e.g., 'Arsenic', 'Salmonella'
    value REAL NOT NULL,
    unit TEXT NOT NULL, -- e.g., 'mg/kg', 'MPN/g'
    is_compliant BOOLEAN,
    FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
);

-- ==========================================
-- Location Module (Destination)
-- ==========================================

-- Sites table: Agricultural fields or disposal sites
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_name TEXT,
    address TEXT,
    region TEXT,
    latitude REAL,
    longitude REAL,
    is_active BOOLEAN DEFAULT 1
);

-- ==========================================
-- Disposal Module (Agronomy)
-- ==========================================

-- Plots table: Sectors within a Site
CREATE TABLE IF NOT EXISTS plots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    name TEXT NOT NULL, -- e.g., 'Sector 1', 'Lote Norte'
    area_hectares REAL,
    crop_type TEXT, -- e.g., 'Corn', 'Wheat'
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

-- Soil Samples table: Analysis of the plot soil
CREATE TABLE IF NOT EXISTS soil_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_id INTEGER NOT NULL,
    sampling_date DATE NOT NULL,
    nitrogen_current REAL,
    phosphorus_current REAL,
    potassium_current REAL,
    ph_level REAL,
    heavy_metals_limit_json TEXT, -- JSON string for limits or current levels
    valid_until DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE
);

-- Applications table: Historical record of sludge application
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plot_id INTEGER NOT NULL,
    application_date DATE NOT NULL,
    total_tonnage_applied REAL,
    nitrogen_load_applied REAL,
    batch_source_ids TEXT, -- Comma separated IDs or JSON of source batches
    notes TEXT,
    FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE
);

-- ==========================================
-- Central Operations Module (The Journey)
-- ==========================================

-- Loads table: The core operational record
CREATE TABLE IF NOT EXISTS loads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT, -- Physical ticket ID if exists (Nullable)
    guide_number TEXT, -- Dispatch Guide Number (Nullable)
    
    -- Relationships
    driver_id INTEGER, -- Nullable at Request
    vehicle_id INTEGER, -- Nullable at Request
    origin_facility_id INTEGER NOT NULL,
    destination_site_id INTEGER, -- Nullable at Request
    batch_id INTEGER, -- Nullable if not assigned yet, but usually required
    
    -- Weights (in Kg)
    weight_gross REAL, -- Truck + Load
    weight_tare REAL,  -- Truck only
    weight_net REAL,   -- Calculated
    
    -- Status and Timing
    status TEXT NOT NULL CHECK (status IN ('Requested', 'Scheduled', 'InTransit', 'Delivered', 'Cancelled')) DEFAULT 'Requested',
    requested_date DATETIME, -- New field for traceability
    scheduled_date DATETIME,
    dispatch_time DATETIME,
    arrival_time DATETIME,
    
    -- Audit
    created_by_user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
    FOREIGN KEY (destination_site_id) REFERENCES sites(id),
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ==========================================
-- Maintenance Module
-- ==========================================

-- Maintenance Events table
CREATE TABLE IF NOT EXISTS maintenance_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER, -- Nullable if it refers to facility equipment
    facility_equipment_id INTEGER, -- Placeholder for future equipment table
    event_date DATE NOT NULL,
    description TEXT NOT NULL,
    maintenance_type TEXT CHECK (maintenance_type IN ('Corrective', 'Preventive')),
    cost REAL,
    performed_by TEXT,
    status TEXT DEFAULT 'Completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
);

-- ==========================================
-- Reporting Views
-- ==========================================

-- View: Full Traceability
-- Purpose: Simplifies complex joins for reporting and dashboards
DROP VIEW IF EXISTS view_full_traceability;
CREATE VIEW view_full_traceability AS
SELECT 
    l.id AS load_id,
    l.ticket_number,
    l.guide_number,
    l.status,
    l.requested_date,
    l.scheduled_date,
    l.dispatch_time,
    l.arrival_time,
    l.weight_gross,
    l.weight_tare,
    l.weight_net,
    
    -- Client & Facility
    c.name AS client_name,
    f.name AS facility_name,
    
    -- Batch Info
    b.batch_code,
    b.class_type,
    
    -- Destination
    s.name AS site_name,
    s.region AS site_region,
    
    -- Transport
    dr.name AS driver_name,
    dr.rut AS driver_rut,
    v.license_plate,
    ctr.name AS contractor_name
    
FROM loads l
LEFT JOIN facilities f ON l.origin_facility_id = f.id
LEFT JOIN clients c ON f.client_id = c.id
LEFT JOIN batches b ON l.batch_id = b.id
LEFT JOIN sites s ON l.destination_site_id = s.id
LEFT JOIN drivers dr ON l.driver_id = dr.id
LEFT JOIN contractors ctr ON dr.contractor_id = ctr.id
LEFT JOIN vehicles v ON l.vehicle_id = v.id;

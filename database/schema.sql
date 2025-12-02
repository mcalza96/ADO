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
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Drivers table: Associated with a contractor
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rut TEXT UNIQUE, -- Renamed from rut_dni in requirements to match convention, mapped in model
    license_number TEXT,
    license_type TEXT, -- New field
    signature_image_path TEXT, -- New field
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Vehicles table: Trucks and trailers
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    brand TEXT,
    model TEXT,
    license_plate TEXT NOT NULL UNIQUE,
    capacity_wet_tons REAL NOT NULL, -- Renamed from max_capacity
    tare_weight REAL NOT NULL, -- In Kg
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Containers table: Roll-off containers (Tolvas)
CREATE TABLE IF NOT EXISTS containers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE, -- Visual ID painted on container, e.g., "TOLVA-204"
    contractor_id INTEGER NOT NULL,
    capacity_m3 REAL NOT NULL, -- Theoretical volume in cubic meters
    status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED')) DEFAULT 'AVAILABLE',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Index for optimized searches by contractor and status
CREATE INDEX IF NOT EXISTS idx_containers_contractor ON containers(contractor_id, status);

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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
    address_reference TEXT,
    region TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    geometry_wkt TEXT, -- Well-Known Text for polygons
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

-- Index for faster lookups by site
CREATE INDEX IF NOT EXISTS idx_plots_site_id ON plots(site_id);

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
    attributes TEXT DEFAULT '{}', -- Flexible JSONB-like storage for variable data (humedad_suelo, velocidad_viento, etc.)
    FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE
);

-- ==========================================
-- Central Operations Module (The Journey)
-- ==========================================

-- Loads table: The core operational record
CREATE TABLE IF NOT EXISTS loads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manifest_code TEXT UNIQUE, -- Generated by system, e.g., "MAN-2025-0001"
    
    -- Relationships
    origin_facility_id INTEGER NOT NULL,
    contractor_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    container_id INTEGER, -- Nullable: not always used
    destination_site_id INTEGER NOT NULL,
    destination_plot_id INTEGER NOT NULL,
    
    -- Operational Data
    material_class TEXT CHECK (material_class IN ('Class A', 'Class B')),
    gross_weight REAL, -- Peso Bruto - Kg
    tare_weight REAL, -- Tara - Kg
    net_weight REAL, -- Calculated: Bruto - Tara
    
    -- Status and Timing
    status TEXT NOT NULL CHECK (status IN ('CREATED', 'IN_TRANSIT', 'ARRIVED', 'COMPLETED', 'CANCELLED')) DEFAULT 'CREATED',
    dispatch_time DATETIME, -- Salida planta
    arrival_time DATETIME, -- Llegada campo
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    attributes TEXT DEFAULT '{}', -- Flexible JSONB-like storage for variable data (ph_inicial, temperatura_llegada, odometro, etc.)
    
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
    FOREIGN KEY (contractor_id) REFERENCES contractors(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (container_id) REFERENCES containers(id),
    FOREIGN KEY (destination_site_id) REFERENCES sites(id),
    FOREIGN KEY (destination_plot_id) REFERENCES plots(id),
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

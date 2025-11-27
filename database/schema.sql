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
    rut TEXT UNIQUE, -- National ID
    license_number TEXT,
    phone TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Vehicles table: Trucks
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    license_plate TEXT NOT NULL UNIQUE,
    tare_weight REAL NOT NULL, -- Weight in Kg
    max_capacity REAL NOT NULL, -- Weight in Kg
    brand TEXT,
    model TEXT,
    year INTEGER,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
);

-- Facilities table: Treatment plants or Origin points
-- Placed here as it is referenced in Routes
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

-- Sites table: Agricultural fields (Destinations)
-- Placed here as it is referenced in Routes
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

-- Routes table: Standard routes definition
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_facility_id INTEGER NOT NULL,
    destination_site_id INTEGER NOT NULL,
    estimated_km REAL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    FOREIGN KEY (destination_site_id) REFERENCES sites(id) ON DELETE CASCADE
);

-- ==========================================
-- Treatment Module (Plant)
-- ==========================================

-- Batches table: Daily production lots
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL,
    batch_code TEXT NOT NULL UNIQUE, -- e.g., 20231027-FAC1
    production_date DATE NOT NULL,
    sludge_type TEXT, -- e.g., 'Centrifuged', 'Dried'
    class_type TEXT CHECK (class_type IN ('A', 'B')),
    initial_tonnage REAL,
    status TEXT DEFAULT 'Open', -- Open, Closed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
);

-- Lab Results table: Linked to Batch
CREATE TABLE IF NOT EXISTS lab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    sample_date DATE NOT NULL,
    ph REAL,
    humidity_percentage REAL,
    dry_matter_percentage REAL,
    nitrogen REAL,
    phosphorus REAL,
    potassium REAL,
    heavy_metals_json TEXT, -- JSON string to store dynamic metals (As, Cd, Hg, Pb, etc.)
    coliforms REAL,
    salmonella_presence BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE
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
    ticket_number TEXT UNIQUE, -- Physical ticket ID if exists
    
    -- Relationships
    driver_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    origin_facility_id INTEGER NOT NULL,
    destination_site_id INTEGER NOT NULL,
    batch_id INTEGER, -- Nullable if not assigned yet, but usually required
    
    -- Weights (in Kg)
    weight_gross REAL, -- Truck + Load
    weight_tare REAL,  -- Truck only
    weight_net REAL,   -- Calculated
    
    -- Status and Timing
    status TEXT NOT NULL CHECK (status IN ('Scheduled', 'InTransit', 'Delivered', 'Cancelled')) DEFAULT 'Scheduled',
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
-- Financial Module (Rates)
-- ==========================================

-- Service Rates table
CREATE TABLE IF NOT EXISTS service_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    route_id INTEGER NOT NULL,
    rate_per_ton REAL,
    rate_per_trip REAL,
    currency TEXT DEFAULT 'CLP',
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_loads_status ON loads(status);
CREATE INDEX idx_loads_date ON loads(scheduled_date);
CREATE INDEX idx_batches_facility ON batches(facility_id);
CREATE INDEX idx_vehicles_contractor ON vehicles(contractor_id);

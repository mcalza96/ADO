-- Migration: Create pickup_requests table and add fields to loads
-- Date: 2025-12-03
-- Description: Implements client pickup request workflow
--              Allows grouping multiple loads from a single client request

-- ==========================================
-- 1. Create pickup_requests table
-- ==========================================
CREATE TABLE IF NOT EXISTS pickup_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    requested_date DATE NOT NULL,
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('BATEA', 'AMPLIROLL')),
    load_quantity INTEGER NOT NULL CHECK (load_quantity > 0),
    containers_per_load INTEGER CHECK (containers_per_load IS NULL OR (containers_per_load >= 1 AND containers_per_load <= 2)),
    notes TEXT,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PARTIALLY_SCHEDULED', 'FULLY_SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_pickup_requests_client ON pickup_requests(client_id, status);
CREATE INDEX IF NOT EXISTS idx_pickup_requests_facility ON pickup_requests(facility_id, requested_date);
CREATE INDEX IF NOT EXISTS idx_pickup_requests_status ON pickup_requests(status, requested_date);

-- ==========================================
-- 2. Add new columns to loads table
-- ==========================================

-- Link to pickup request (groups loads from same client request)
ALTER TABLE loads ADD COLUMN pickup_request_id INTEGER REFERENCES pickup_requests(id);

-- Vehicle type requested by client (BATEA/AMPLIROLL)
ALTER TABLE loads ADD COLUMN vehicle_type_requested TEXT;

-- Container quantity for this load (AMPLIROLL: 1-2)
ALTER TABLE loads ADD COLUMN container_quantity INTEGER;

-- Index for pickup request lookups
CREATE INDEX IF NOT EXISTS idx_loads_pickup_request ON loads(pickup_request_id);

#!/usr/bin/env python3
"""
Migration Script: Apply pickup_requests treatment plant support
Applies migration 017 to add treatment_plant_id and make client_id/facility_id nullable
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "database/biosolids.db"

def apply_migration():
    """Apply the migration for pickup_requests treatment plant support."""
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied (treatment_plant_id exists)
        cursor.execute("PRAGMA table_info(pickup_requests)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "treatment_plant_id" in columns:
            print("Migration already applied: treatment_plant_id column exists")
            conn.close()
            return True
        
        print("Applying migration 017: pickup_requests treatment plant support...")
        
        # Step 1: Create new table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pickup_requests_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                facility_id INTEGER,
                treatment_plant_id INTEGER,
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
                FOREIGN KEY (facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
                FOREIGN KEY (treatment_plant_id) REFERENCES treatment_plants(id) ON DELETE CASCADE,
                CHECK (facility_id IS NOT NULL OR treatment_plant_id IS NOT NULL)
            )
        """)
        
        # Step 2: Check if old table exists and copy data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pickup_requests'")
        if cursor.fetchone():
            print("Copying existing data...")
            cursor.execute("""
                INSERT INTO pickup_requests_new (
                    id, client_id, facility_id, treatment_plant_id, requested_date, 
                    vehicle_type, load_quantity, containers_per_load, notes, 
                    status, is_active, created_at, updated_at
                )
                SELECT 
                    id, client_id, facility_id, NULL, requested_date,
                    vehicle_type, load_quantity, containers_per_load, notes,
                    status, is_active, created_at, updated_at
                FROM pickup_requests
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE pickup_requests")
            print("Old table dropped")
        
        # Step 3: Rename new table
        cursor.execute("ALTER TABLE pickup_requests_new RENAME TO pickup_requests")
        print("New table renamed to pickup_requests")
        
        # Step 4: Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pickup_requests_client 
            ON pickup_requests(client_id, status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pickup_requests_facility 
            ON pickup_requests(facility_id, requested_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pickup_requests_status 
            ON pickup_requests(status, requested_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pickup_requests_treatment_plant 
            ON pickup_requests(treatment_plant_id, status)
        """)
        print("Indexes created")
        
        conn.commit()
        print("Migration 017 applied successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    apply_migration()

import sqlite3

DB_PATH = "database/biosolids.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Rename old table
        print("Renaming old table...")
        cursor.execute("ALTER TABLE loads RENAME TO loads_old;")
        
        # 2. Create new table with relaxed constraints
        print("Creating new table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS loads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT,
            guide_number TEXT,
            
            -- Relationships
            driver_id INTEGER, -- Nullable at Request
            vehicle_id INTEGER, -- Nullable at Request
            origin_facility_id INTEGER NOT NULL,
            destination_site_id INTEGER, -- Nullable at Request
            batch_id INTEGER, -- Nullable
            
            -- Weights (in Kg)
            weight_gross REAL,
            weight_tare REAL,
            weight_net REAL,
            
            -- Status and Timing
            status TEXT NOT NULL CHECK (status IN ('Requested', 'Scheduled', 'InTransit', 'Delivered', 'Cancelled')) DEFAULT 'Requested',
            requested_date DATETIME,
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
        """)
        
        # 3. Copy data
        # Note: We need to map columns correctly. 
        # Old table might not have 'guide_number' if it wasn't added before, 
        # but we added 'requested_date' manually.
        # Let's check columns of loads_old first to be safe, or just select common ones.
        # For MVP, assuming standard structure + requested_date.
        
        print("Copying data...")
        # We explicitly list columns to avoid mismatch if order changed
        cursor.execute("""
        INSERT INTO loads (
            id, ticket_number, driver_id, vehicle_id, origin_facility_id, 
            destination_site_id, batch_id, weight_gross, weight_tare, weight_net, 
            status, scheduled_date, dispatch_time, arrival_time, 
            created_by_user_id, created_at, updated_at, requested_date
        )
        SELECT 
            id, ticket_number, driver_id, vehicle_id, origin_facility_id, 
            destination_site_id, batch_id, weight_gross, weight_tare, weight_net, 
            status, scheduled_date, dispatch_time, arrival_time, 
            created_by_user_id, created_at, updated_at, requested_date
        FROM loads_old;
        """)
        
        # 4. Drop old table
        print("Dropping old table...")
        cursor.execute("DROP TABLE loads_old;")
        
        conn.commit()
        print("Migration successful!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

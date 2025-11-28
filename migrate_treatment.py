import sqlite3

DB_PATH = "database/biosolids.db"

def migrate():
    print(f"Migrating database (Treatment Context) at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Create treatment_plants table
        print("Creating treatment_plants table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS treatment_plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            authorization_resolution TEXT,
            latitude REAL,
            longitude REAL,
            is_active BOOLEAN DEFAULT 1
        );
        """)
        
        # 2. Add columns to loads table
        print("Adding columns to loads table...")
        
        cursor.execute("PRAGMA table_info(loads)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "destination_treatment_plant_id" not in columns:
            cursor.execute("ALTER TABLE loads ADD COLUMN destination_treatment_plant_id INTEGER REFERENCES treatment_plants(id)")
            print("Added destination_treatment_plant_id")
            
        if "reception_time" not in columns:
            cursor.execute("ALTER TABLE loads ADD COLUMN reception_time DATETIME")
            print("Added reception_time")
            
        if "discharge_time" not in columns:
            cursor.execute("ALTER TABLE loads ADD COLUMN discharge_time DATETIME")
            print("Added discharge_time")
            
        if "quality_ph" not in columns:
            cursor.execute("ALTER TABLE loads ADD COLUMN quality_ph REAL")
            print("Added quality_ph")
            
        if "quality_humidity" not in columns:
            cursor.execute("ALTER TABLE loads ADD COLUMN quality_humidity REAL")
            print("Added quality_humidity")

        # 3. Update Status Enum to include 'PendingReception' (At Treatment Plant)
        # We need to recreate the table again to update the CHECK constraint if we want a new status.
        # Or we can reuse 'PendingDisposal' but that's confusing.
        # Let's add 'PendingReception' and 'Treated' (or 'ReceivedAtPlant').
        # Actually, the requirement says: "Bandeja de Entrada... cuando un chofer marca Llegada a Destino".
        # If destination is Treatment, status should be 'PendingReception'.
        # Let's do a full migration of loads table to update Enum.
        
        print("Updating Status Enum...")
        cursor.execute("ALTER TABLE loads RENAME TO loads_temp_v4;")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS loads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT,
            guide_number TEXT,
            
            -- Relationships
            driver_id INTEGER,
            vehicle_id INTEGER,
            origin_facility_id INTEGER NOT NULL,
            destination_site_id INTEGER,
            batch_id INTEGER,
            
            -- Weights
            weight_gross REAL,
            weight_tare REAL,
            weight_net REAL,
            
            -- Status (Updated)
            status TEXT NOT NULL CHECK (status IN ('Requested', 'Scheduled', 'InTransit', 'PendingDisposal', 'PendingReception', 'Treated', 'Disposed', 'Cancelled')) DEFAULT 'Requested',
            
            -- Dates
            requested_date DATETIME,
            scheduled_date DATETIME,
            dispatch_time DATETIME,
            arrival_time DATETIME,
            
            -- Disposal Traceability
            disposal_time DATETIME,
            disposal_coordinates TEXT,
            treatment_facility_id INTEGER,
            
            -- Hybrid Logistics
            destination_treatment_plant_id INTEGER,
            reception_time DATETIME,
            discharge_time DATETIME,
            quality_ph REAL,
            quality_humidity REAL,
            
            -- Audit
            created_by_user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (driver_id) REFERENCES drivers(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
            FOREIGN KEY (destination_site_id) REFERENCES sites(id),
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (treatment_facility_id) REFERENCES facilities(id),
            FOREIGN KEY (destination_treatment_plant_id) REFERENCES treatment_plants(id)
        );
        """)
        
        print("Copying data...")
        cursor.execute("""
        INSERT INTO loads (
            id, ticket_number, guide_number, driver_id, vehicle_id, origin_facility_id, 
            destination_site_id, batch_id, weight_gross, weight_tare, weight_net, 
            status, requested_date, scheduled_date, dispatch_time, arrival_time,
            disposal_time, disposal_coordinates, treatment_facility_id,
            destination_treatment_plant_id, reception_time, discharge_time, quality_ph, quality_humidity,
            created_by_user_id, created_at, updated_at
        )
        SELECT 
            id, ticket_number, guide_number, driver_id, vehicle_id, origin_facility_id, 
            destination_site_id, batch_id, weight_gross, weight_tare, weight_net, 
            status, requested_date, scheduled_date, dispatch_time, arrival_time,
            disposal_time, disposal_coordinates, treatment_facility_id,
            destination_treatment_plant_id, reception_time, discharge_time, quality_ph, quality_humidity,
            created_by_user_id, created_at, updated_at
        FROM loads_temp_v4;
        """)
        
        cursor.execute("DROP TABLE loads_temp_v4;")

        conn.commit()
        print("Migration successful!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

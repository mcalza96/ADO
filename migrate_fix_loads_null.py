import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate_fix_null_constraint():
    print("Starting Migration to fix NOT NULL constraint on origin_facility_id...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Rename existing table
        cursor.execute("ALTER TABLE loads RENAME TO loads_old")
        
        # 2. Create new table with nullable origin_facility_id
        # We also clean up the schema to include all current columns
        create_table_sql = """
        CREATE TABLE loads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT,
            guide_number TEXT,
            
            -- Relationships
            driver_id INTEGER,
            vehicle_id INTEGER,
            origin_facility_id INTEGER, -- Nullable now
            destination_site_id INTEGER,
            batch_id INTEGER,
            
            -- Weights
            weight_gross REAL,
            weight_tare REAL,
            weight_net REAL,
            
            -- Status
            status TEXT DEFAULT 'Requested',
            
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
            
            -- Added Columns
            container_1_id INTEGER,
            container_2_id INTEGER,
            origin_treatment_plant_id INTEGER,
            batch_1_id INTEGER,
            batch_2_id INTEGER,
            
            -- Foreign Keys
            FOREIGN KEY (driver_id) REFERENCES drivers(id),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (origin_facility_id) REFERENCES facilities(id),
            FOREIGN KEY (destination_site_id) REFERENCES sites(id),
            FOREIGN KEY (batch_id) REFERENCES batches(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (treatment_facility_id) REFERENCES facilities(id),
            FOREIGN KEY (destination_treatment_plant_id) REFERENCES treatment_plants(id)
        )
        """
        cursor.execute(create_table_sql)
        
        # 3. Copy data
        # We need to list columns explicitly to avoid mismatch if we dropped some unused ones
        # We are dropping treatment_batch_1_id and treatment_batch_2_id as they were replaced by batch_1_id/batch_2_id
        
        columns_to_copy = [
            "id", "ticket_number", "guide_number", "driver_id", "vehicle_id", 
            "origin_facility_id", "destination_site_id", "batch_id", 
            "weight_gross", "weight_tare", "weight_net", "status", 
            "requested_date", "scheduled_date", "dispatch_time", "arrival_time", 
            "disposal_time", "disposal_coordinates", "treatment_facility_id", 
            "destination_treatment_plant_id", "reception_time", "discharge_time", 
            "quality_ph", "quality_humidity", "created_by_user_id", 
            "created_at", "updated_at", "container_1_id", "container_2_id", 
            "origin_treatment_plant_id", "batch_1_id", "batch_2_id"
        ]
        
        cols_str = ", ".join(columns_to_copy)
        
        insert_sql = f"INSERT INTO loads ({cols_str}) SELECT {cols_str} FROM loads_old"
        cursor.execute(insert_sql)
        
        # 4. Drop old table
        cursor.execute("DROP TABLE loads_old")
        
        conn.commit()
        print("Migration successful: origin_facility_id is now nullable.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_fix_null_constraint()

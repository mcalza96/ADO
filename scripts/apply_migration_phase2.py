import sqlite3
import os
from datetime import datetime

DB_PATH = "database/biosolids.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Update Drivers Table
        print("Updating drivers table...")
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drivers'")
        if not cursor.fetchone():
            print("Creating drivers table...")
            cursor.execute("""
            CREATE TABLE drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contractor_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                rut TEXT UNIQUE,
                license_number TEXT,
                license_type TEXT,
                signature_image_path TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
            );
            """)
        else:
            # Check for new columns and add if missing
            columns = [info[1] for info in cursor.execute("PRAGMA table_info(drivers)")]
            
            if 'license_type' not in columns:
                print("Adding license_type to drivers...")
                cursor.execute("ALTER TABLE drivers ADD COLUMN license_type TEXT")
            
            if 'signature_image_path' not in columns:
                print("Adding signature_image_path to drivers...")
                cursor.execute("ALTER TABLE drivers ADD COLUMN signature_image_path TEXT")
                
            if 'created_at' not in columns:
                print("Adding created_at to drivers...")
                # SQLite limitation: Cannot use CURRENT_TIMESTAMP in ADD COLUMN
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN created_at DATETIME DEFAULT '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'")
                
            if 'updated_at' not in columns:
                print("Adding updated_at to drivers...")
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN updated_at DATETIME DEFAULT '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'")

        # 2. Update Vehicles Table
        print("Updating vehicles table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles'")
        if not cursor.fetchone():
             print("Creating vehicles table...")
             cursor.execute("""
            CREATE TABLE vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contractor_id INTEGER NOT NULL,
                brand TEXT,
                model TEXT,
                license_plate TEXT NOT NULL UNIQUE,
                capacity_wet_tons REAL NOT NULL,
                tare_weight REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
            );
            """)
        else:
            columns = [info[1] for info in cursor.execute("PRAGMA table_info(vehicles)")]
            
            # Rename max_capacity to capacity_wet_tons if needed
            # SQLite doesn't support renaming columns easily in older versions, but we can check if new one exists
            if 'capacity_wet_tons' not in columns:
                if 'max_capacity' in columns:
                    print("Renaming max_capacity to capacity_wet_tons in vehicles...")
                    cursor.execute("ALTER TABLE vehicles RENAME COLUMN max_capacity TO capacity_wet_tons")
                else:
                    print("Adding capacity_wet_tons to vehicles...")
                    cursor.execute("ALTER TABLE vehicles ADD COLUMN capacity_wet_tons REAL DEFAULT 0")

            if 'created_at' not in columns:
                print("Adding created_at to vehicles...")
                cursor.execute(f"ALTER TABLE vehicles ADD COLUMN created_at DATETIME DEFAULT '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'")
                
            if 'updated_at' not in columns:
                print("Adding updated_at to vehicles...")
                cursor.execute(f"ALTER TABLE vehicles ADD COLUMN updated_at DATETIME DEFAULT '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

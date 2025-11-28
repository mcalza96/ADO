import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate_vehicle_types():
    print("Starting Vehicle Type Migration...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check columns in vehicles
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'type' not in columns:
        try:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN type TEXT DEFAULT 'BATEA'")
            print("Added 'type' to vehicles (Default: BATEA).")
        except Exception as e:
            print(f"Error adding type: {e}")
            
    conn.commit()
    conn.close()
    print("Vehicle Type Migration Completed.")

if __name__ == "__main__":
    migrate_vehicle_types()

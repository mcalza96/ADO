import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate_ds4():
    print("Starting DS4 & Container Migration...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create Containers Table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'AVAILABLE',
                current_plant_id INTEGER
            )
        """)
        print("Created 'containers' table.")
    except Exception as e:
        print(f"Error creating containers table: {e}")

    # 2. Create Treatment Batches Table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treatment_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                container_id INTEGER NOT NULL,
                fill_time TIMESTAMP NOT NULL,
                ph_0h REAL,
                ph_2h REAL,
                ph_24h REAL,
                humidity REAL,
                status TEXT DEFAULT 'MONITORING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(plant_id) REFERENCES treatment_plants(id),
                FOREIGN KEY(container_id) REFERENCES containers(id)
            )
        """)
        print("Created 'treatment_batches' table.")
    except Exception as e:
        print(f"Error creating treatment_batches table: {e}")

    # 3. Alter Loads Table
    # Check if columns exist first to avoid errors on re-run
    cursor.execute("PRAGMA table_info(loads)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'container_1_id' not in columns:
        try:
            cursor.execute("ALTER TABLE loads ADD COLUMN container_1_id INTEGER")
            print("Added 'container_1_id' to loads.")
        except Exception as e:
            print(f"Error adding container_1_id: {e}")
            
    if 'container_2_id' not in columns:
        try:
            cursor.execute("ALTER TABLE loads ADD COLUMN container_2_id INTEGER")
            print("Added 'container_2_id' to loads.")
        except Exception as e:
            print(f"Error adding container_2_id: {e}")

    if 'origin_treatment_plant_id' not in columns:
        try:
            cursor.execute("ALTER TABLE loads ADD COLUMN origin_treatment_plant_id INTEGER")
            print("Added 'origin_treatment_plant_id' to loads.")
        except Exception as e:
            print(f"Error adding origin_treatment_plant_id: {e}")

    conn.commit()
    conn.close()
    print("DS4 Migration Completed.")

if __name__ == "__main__":
    migrate_ds4()

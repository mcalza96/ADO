import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Attempting to add 'allowed_vehicle_types' column to 'facilities' table...")
        cursor.execute("ALTER TABLE facilities ADD COLUMN allowed_vehicle_types TEXT")
        print("Column 'allowed_vehicle_types' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'allowed_vehicle_types' already exists.")
        else:
            print(f"Error adding column: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()

import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate_dispatch_linkage():
    print("Starting Dispatch Linkage Migration...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check columns in loads
    cursor.execute("PRAGMA table_info(loads)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'batch_1_id' not in columns:
        try:
            cursor.execute("ALTER TABLE loads ADD COLUMN batch_1_id INTEGER")
            print("Added 'batch_1_id' to loads.")
        except Exception as e:
            print(f"Error adding batch_1_id: {e}")
            
    if 'batch_2_id' not in columns:
        try:
            cursor.execute("ALTER TABLE loads ADD COLUMN batch_2_id INTEGER")
            print("Added 'batch_2_id' to loads.")
        except Exception as e:
            print(f"Error adding batch_2_id: {e}")

    conn.commit()
    conn.close()
    print("Dispatch Linkage Migration Completed.")

if __name__ == "__main__":
    migrate_dispatch_linkage()

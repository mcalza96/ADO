import sqlite3
import os

DB_PATH = "database/biosolids.db"

def run_migration():
    print("🚀 Applying migration...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        with open("database/migrations/add_tto03_columns.sql", "r") as f:
            sql_script = f.read()
            
        cursor.executescript(sql_script)
        conn.commit()
        print("✅ Migration applied successfully!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️ Columns might already exist. Skipping.")
        else:
            print(f"❌ Error applying migration: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()

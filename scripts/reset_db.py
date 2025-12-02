import sqlite3
import os
import time

DB_PATH = "ado_system.db"
SCHEMA_PATH = "database/schema.sql"
MIGRATIONS_DIR = "migrations"

def reset_db():
    abs_path = os.path.abspath(DB_PATH)
    print(f"🗑️  Resetting database: {abs_path}")
    
    # 1. Remove existing DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ Deleted existing database file")
        time.sleep(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 2. Apply Base Schema
    print(f"📜 Applying schema: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
        
    # 3. Apply Migrations in order
    migrations = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
    
    for migration in migrations:
        print(f"🚀 Applying migration: {migration}")
        with open(os.path.join(MIGRATIONS_DIR, migration), 'r') as f:
            migration_sql = f.read()
            try:
                cursor.executescript(migration_sql)
            except Exception as e:
                print(f"⚠️  Warning applying {migration}: {e}")
                
    conn.commit()
    conn.close()
    print("✨ Database reset complete!")

if __name__ == "__main__":
    reset_db()

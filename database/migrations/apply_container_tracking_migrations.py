#!/usr/bin/env python3
"""
Apply container filling records migrations.

Run this script to create the container_filling_records table and add arrival_ph to loads.
"""
import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DB_PATH


def apply_migrations():
    """Apply the new migrations for container tracking."""
    db_path = DB_PATH
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please run the application first to create the database.")
        return False
    
    migrations_dir = Path(__file__).parent
    
    migrations = [
        "018_container_filling_records.sql",
        "019_add_arrival_ph.sql"
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for migration_file in migrations:
        migration_path = migrations_dir / migration_file
        if not migration_path.exists():
            print(f"Migration file not found: {migration_path}")
            continue
        
        print(f"Applying migration: {migration_file}")
        
        try:
            with open(migration_path, 'r') as f:
                sql = f.read()
            
            # Execute each statement separately (SQLite doesn't support multiple statements in execute)
            statements = sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        print(f"  ✓ Executed: {statement[:50]}...")
                    except sqlite3.OperationalError as e:
                        if "already exists" in str(e) or "duplicate column" in str(e):
                            print(f"  ⏭ Skipped (already exists): {statement[:50]}...")
                        else:
                            print(f"  ✗ Error: {e}")
                            print(f"    Statement: {statement}")
            
            conn.commit()
            print(f"  ✓ Migration {migration_file} applied successfully")
            
        except Exception as e:
            print(f"  ✗ Error applying migration {migration_file}: {e}")
            conn.rollback()
    
    conn.close()
    print("\nMigrations completed!")
    return True


if __name__ == "__main__":
    apply_migrations()


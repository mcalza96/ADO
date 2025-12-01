#!/usr/bin/env python3
"""
Migration script for Container table refactoring.
Converts old schema (code, status, current_plant_id) 
to new Roll-off schema (code, contractor_id, capacity_m3, status).
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import db_manager
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager


def migrate_containers(db_path: str = "database/biosolids.db"):
    """
    Migrates containers table to new schema.
    
    CRITICAL WARNING: This drops the old containers table.
    Backup your database before running this script!
    """
    print("=" * 60)
    print("Container Table Migration Script")
    print("=" * 60)
    print(f"Target database: {db_path}")
    print()
    
    # Ask for confirmation
    response = input("⚠️  WARNING: This will DROP the existing 'containers' table.\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if containers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='containers'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            print("📊 Backing up existing data...")
            cursor.execute("SELECT * FROM containers")
            old_data = cursor.fetchall()
            print(f"   Found {len(old_data)} existing containers")
            
            # Drop old table
            print("🗑️  Dropping old containers table...")
            cursor.execute("DROP TABLE IF EXISTS containers")
            cursor.execute("DROP INDEX IF EXISTS idx_containers_contractor")
        
        # Create new table with Roll-off schema
        print("🏗️  Creating new containers table...")
        cursor.execute("""
            CREATE TABLE containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                contractor_id INTEGER NOT NULL,
                capacity_m3 REAL NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED')) DEFAULT 'AVAILABLE',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE
            )
        """)
        
        # Create index
        print("📑 Creating index...")
        cursor.execute("CREATE INDEX idx_containers_contractor ON containers(contractor_id, status)")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print()
        print("⚠️  NOTE: Old container data was NOT migrated.")
        print("   You need to re-create containers with contractor assignment and capacity.")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_containers()

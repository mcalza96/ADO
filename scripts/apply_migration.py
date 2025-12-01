"""
Script to apply SQL migration: Add audit fields for Soft Delete support.

This script applies the migration 001_add_audit_fields.sql to the database.
It adds is_active, created_at, and updated_at fields to the clients, facilities,
and contractors tables.

Usage:
    python scripts/apply_migration.py migrations/001_add_audit_fields.sql
"""

import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import DB_PATH


def apply_migration(migration_file: str):
    """
    Apply a SQL migration file to the database.
    
    Args:
        migration_file: Path to the migration SQL file
    """
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Applying Migration: {os.path.basename(migration_file)}")
    print(f"{'='*60}\n")
    
    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Apply migration
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Execute migration (handle multiple statements)
        cursor.executescript(migration_sql)
        
        conn.commit()
        print(f"✅ Migration applied successfully!")
        print(f"   Database: {DB_PATH}\n")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Error applying migration: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_migration.py <migration_file>")
        print("\nExample:")
        print("  python scripts/apply_migration.py migrations/001_add_audit_fields.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    apply_migration(migration_file)

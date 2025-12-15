"""
Apply migration 026_add_contractor_type.sql

This migration adds the contractor_type column to the contractors table
to support different types of contractors (TRANSPORT, DISPOSAL, etc.)

Usage:
    python database/migrations/apply_026_migration.py
"""

import sqlite3
import os

def apply_migration():
    """Apply the contractor type migration."""
    db_path = "database/biosolids.db"
    migration_path = "database/migrations/026_add_contractor_type.sql"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(contractors)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "contractor_type" in columns:
            print("Migration 026 already applied: contractor_type column exists.")
            conn.close()
            return True
        
        print("Applying migration 026: Adding contractor_type column...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE contractors 
            ADD COLUMN contractor_type TEXT DEFAULT 'TRANSPORT'
            CHECK (contractor_type IN ('TRANSPORT', 'DISPOSAL', 'SERVICES', 'MECHANICS'))
        """)
        
        # Update existing records
        cursor.execute("UPDATE contractors SET contractor_type = 'TRANSPORT' WHERE contractor_type IS NULL")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contractors_type ON contractors(contractor_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contractors_type_active ON contractors(contractor_type, is_active)")
        
        conn.commit()
        print("Migration 026 applied successfully!")
        print(f"  - Added contractor_type column with default 'TRANSPORT'")
        print(f"  - Updated existing records to TRANSPORT")
        print(f"  - Created indexes for contractor_type")
        
        # Show summary
        cursor.execute("SELECT contractor_type, COUNT(*) FROM contractors GROUP BY contractor_type")
        summary = cursor.fetchall()
        if summary:
            print("\nContractor distribution by type:")
            for ctype, count in summary:
                print(f"  - {ctype}: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error applying migration 026: {str(e)}")
        return False


if __name__ == "__main__":
    apply_migration()

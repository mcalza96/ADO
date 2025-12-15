"""
Apply migration 023_disposal_site_tariffs.sql

Crea la tabla disposal_site_tariffs para almacenar las tarifas
que los sitios de disposición cobran por recibir residuos.

Usage:
    python database/migrations/apply_023_migration.py
"""

import sqlite3
import os

def apply_migration():
    """Apply the disposal site tariffs migration."""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'biosolids.db')
    db_path = os.path.abspath(db_path)
    
    # Get migration SQL file
    migration_path = os.path.join(os.path.dirname(__file__), '023_disposal_site_tariffs.sql')
    
    if not os.path.exists(migration_path):
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    # Read migration SQL
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    # Apply migration
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute migration
        cursor.executescript(migration_sql)
        conn.commit()
        
        # Verify table was created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='disposal_site_tariffs'
        """)
        
        if cursor.fetchone():
            print("✅ Migration 023_disposal_site_tariffs applied successfully!")
            print("   Created table: disposal_site_tariffs")
            
            # Check if there are any sites to show a helpful message
            cursor.execute("SELECT COUNT(*) FROM sites WHERE is_active = 1")
            site_count = cursor.fetchone()[0]
            
            if site_count > 0:
                print(f"\n💡 Tienes {site_count} sitios activos.")
                print("   Para configurar tarifas de disposición, ejecuta:")
                print("   INSERT INTO disposal_site_tariffs (site_id, rate_uf, valid_from)")
                print("   VALUES (<site_id>, 0.24, DATE('now'));")
            else:
                print("\n⚠️ No hay sitios activos en el sistema.")
        else:
            print("❌ Table was not created")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error applying migration: {str(e)}")
        return False


if __name__ == "__main__":
    apply_migration()

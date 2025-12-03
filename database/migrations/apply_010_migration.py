#!/usr/bin/env python3
"""
Script to safely add missing columns to the loads table.
Handles the case where columns may already exist.
"""

import sqlite3
import os

DB_PATH = "ado_system.db"

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_column_if_not_exists(cursor, table_name, column_name, column_type, default=None):
    """Add a column to a table if it doesn't already exist."""
    if not column_exists(cursor, table_name, column_name):
        default_clause = f" DEFAULT {default}" if default is not None else ""
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"
        print(f"Adding column: {column_name}")
        cursor.execute(sql)
        return True
    else:
        print(f"Column {column_name} already exists, skipping")
        return False

def main():
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "..", "..", DB_PATH)
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # List of columns to add
        columns_to_add = [
            ("ticket_number", "TEXT", None),
            ("guide_number", "TEXT", None),
            ("requested_date", "DATE", None),
            ("scheduled_date", "DATE", None),
            ("batch_id", "INTEGER", None),
        ]
        
        added_count = 0
        for col_name, col_type, default in columns_to_add:
            if add_column_if_not_exists(cursor, "loads", col_name, col_type, default):
                added_count += 1
        
        # Commit changes
        conn.commit()
        print(f"\nMigration complete! Added {added_count} new column(s).")
        
        # Recreate the view
        print("\nRecreating view_full_traceability...")
        cursor.execute("DROP VIEW IF EXISTS view_full_traceability")
        
        create_view_sql = """
        CREATE VIEW view_full_traceability AS
        SELECT 
            l.id AS load_id,
            COALESCE(l.ticket_number, '') AS ticket_number,
            COALESCE(l.guide_number, '') AS guide_number,
            l.status,
            l.requested_date,
            l.scheduled_date,
            l.dispatch_time,
            l.arrival_time,
            l.gross_weight AS weight_gross,
            l.tare_weight AS weight_tare,
            COALESCE(l.net_weight, (COALESCE(l.gross_weight, 0) - COALESCE(l.tare_weight, 0))) AS weight_net,
            
            -- Client & Facility
            c.name AS client_name,
            f.name AS facility_name,
            
            -- Batch Info
            b.batch_code,
            b.class_type,
            
            -- Destination
            s.name AS site_name,
            s.region AS site_region,
            
            -- Transport
            dr.name AS driver_name,
            dr.rut AS driver_rut,
            v.license_plate,
            ctr.name AS contractor_name
            
        FROM loads l
        LEFT JOIN facilities f ON l.origin_facility_id = f.id
        LEFT JOIN clients c ON f.client_id = c.id
        LEFT JOIN batches b ON l.batch_id = b.id
        LEFT JOIN sites s ON l.destination_site_id = s.id
        LEFT JOIN drivers dr ON l.driver_id = dr.id
        LEFT JOIN contractors ctr ON dr.contractor_id = ctr.id
        LEFT JOIN vehicles v ON l.vehicle_id = v.id
        """
        
        cursor.execute(create_view_sql)
        conn.commit()
        print("View recreated successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()

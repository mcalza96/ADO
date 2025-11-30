import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from services.reporting.reporting_service import ReportingService
from database.db_manager import DatabaseManager

def test_reporting_service():
    print("Testing Reporting Service...")
    service = ReportingService()
    
    # Test 1: Get Client Report
    print("\n1. Testing get_client_report...")
    try:
        df_client = service.get_client_report()
        print(f"   Success. Rows returned: {len(df_client)}")
        print(f"   Columns: {list(df_client.columns)}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Test 2: Get Fleet Monitoring
    print("\n2. Testing get_fleet_monitoring...")
    try:
        df_fleet = service.get_fleet_monitoring()
        print(f"   Success. Rows returned: {len(df_fleet)}")
        if not df_fleet.empty:
            print(f"   Sample hours_elapsed: {df_fleet['hours_elapsed'].iloc[0]}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Test 3: Get Agronomy Stats
    print("\n3. Testing get_site_agronomy_stats...")
    try:
        # Get a site id first
        with DatabaseManager() as conn:
            site = conn.execute("SELECT id FROM sites LIMIT 1").fetchone()
            
        if site:
            site_id = site[0]
            df_agronomy = service.get_site_agronomy_stats(site_id)
            print(f"   Success for Site ID {site_id}. Rows returned: {len(df_agronomy)}")
            if not df_agronomy.empty:
                print(f"   Columns: {list(df_agronomy.columns)}")
        else:
            print("   Skipping (No sites found in DB)")
    except Exception as e:
        print(f"   Failed: {e}")

if __name__ == "__main__":
    test_reporting_service()

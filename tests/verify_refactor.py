import sys
import os
import datetime
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['streamlit'] = MagicMock()
sys.modules['fpdf'] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from services.operations.dispatch_service import DispatchService
from services.operations.site_preparation_service import SitePreparationService
from services.masters.transport_service import TransportService
from services.operations.batch_service import BatchService
from container import get_container

def test_refactor():
    print("Testing Refactored Services...")
    
    # 1. Test Container Registration
    try:
        services = get_container()
        if hasattr(services, 'manifest_service') and hasattr(services, 'site_prep_service'):
            print("✅ New services registered in container.")
        else:
            print("❌ New services NOT registered in container.")
            return
    except Exception as e:
        print(f"❌ Container initialization failed: {e}")
        return

    # 2. Test SitePreparationService
    try:
        # Mock DB Manager for simple instantiation check
        db_path = "/tmp/test_refactor.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        db_manager = DatabaseManager(db_path)
        
        # Initialize schema for site events
        with db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS site_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    event_type TEXT,
                    event_date TIMESTAMP,
                    description TEXT,
                    created_at TIMESTAMP
                )
            """)
            
        site_prep = SitePreparationService(db_manager)
        site_prep.register_site_event(1, "Test Event", datetime.datetime.now(), "Test Description")
        events = site_prep.get_site_events(1)
        
        if len(events) == 1:
            print("✅ SitePreparationService works correctly.")
        else:
            print(f"❌ SitePreparationService failed. Found {len(events)} events.")
            
    except Exception as e:
        print(f"❌ SitePreparationService test failed: {e}")

    # 3. Test TransportService get_driver_loads
    try:
        transport = TransportService(db_manager)
        if hasattr(transport, 'get_driver_loads'):
            print("✅ TransportService has get_driver_loads method.")
        else:
            print("❌ TransportService missing get_driver_loads method.")
            
    except Exception as e:
        print(f"❌ TransportService test failed: {e}")

if __name__ == "__main__":
    test_refactor()

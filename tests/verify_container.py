import sys
import os
from unittest.mock import MagicMock

# Mock streamlit before importing container
sys.modules['streamlit'] = MagicMock()
sys.modules['fpdf'] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from container import get_container

def test_container():
    try:
        services = get_container()
        if hasattr(services, 'location_service'):
            print("✅ Location Service is registered in the container.")
            # Verify it has get_facility_by_id
            if hasattr(services.location_service, 'get_facility_by_id'):
                print("✅ Location Service has get_facility_by_id method.")
            else:
                print("❌ Location Service missing get_facility_by_id method.")
        else:
            print("❌ Location Service is NOT registered in the container.")
            
    except Exception as e:
        print(f"❌ Error initializing container: {e}")

if __name__ == "__main__":
    test_container()

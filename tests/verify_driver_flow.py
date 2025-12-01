import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from repositories.vehicle_repository import VehicleRepository
from services.operations.dispatch_service import DispatchService
from models.operations.load import Load

# Mock Streamlit for Container
from unittest.mock import MagicMock
sys.modules['streamlit'] = MagicMock()
import streamlit
streamlit.cache_resource = lambda func: func

# Mock fpdf
sys.modules['fpdf'] = MagicMock()

from container import get_container

def verify_driver_flow():
    print("🚀 Starting Driver Flow Verification...")
    
    # Use container to get services (simulating UI usage)
    services = get_container()
    dispatch_service = services.dispatch_service
    load_repo = services.transport_service.load_repo
    vehicle_repo = services.transport_service.vehicle_repo
    
    # 1. Setup: Get or Create Vehicle
    print("1️⃣ Setting up environment...")
    vehicles = vehicle_repo.get_all_active()
    if not vehicles:
        print("   ⚠️ No active vehicles found. Please ensure seed data exists.")
        return
    
    vehicle = vehicles[0]
    print(f"   ✅ Using Vehicle: {vehicle.license_plate} (ID: {vehicle.id})")
    
    # 2. Create a Scheduled Load
    print("2️⃣ Creating Scheduled Load...")
    scheduled_load = Load(
        id=None,
        origin_facility_id=1, # Assuming ID 1 exists
        destination_site_id=1, # Assuming ID 1 exists
        vehicle_id=vehicle.id,
        driver_id=1, # Assuming ID 1 exists
        status='Scheduled',
        scheduled_date=datetime.now(),
        created_at=datetime.now()
    )
    
    created_load = load_repo.add(scheduled_load)
    load_id = created_load.id
    print(f"   ✅ Load created with ID: {load_id} (Status: {created_load.status})")
    
    # 3. Accept Trip
    print("3️⃣ Driver Accepts Trip...")
    dispatch_service.accept_trip(load_id)
    
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Accepted', f"Expected 'Accepted', got '{load.status}'"
    print(f"   ✅ Status is '{load.status}'")
    
    # 4. Start Trip
    print("4️⃣ Driver Starts Trip (Gate Out)...")
    dispatch_service.start_trip(load_id)
    
    load = load_repo.get_by_id(load_id)
    assert load.status == 'InTransit', f"Expected 'InTransit', got '{load.status}'"
    print(f"   ✅ Status is '{load.status}'")
    
    # 5. Register Arrival
    print("5️⃣ Driver Arrives at Destination (Gate In)...")
    dispatch_service.register_arrival(load_id)
    
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Arrived', f"Expected 'Arrived', got '{load.status}'"
    print(f"   ✅ Status is '{load.status}'")
    
    # 6. Close Trip
    print("6️⃣ Driver Closes Trip (Delivery)...")
    close_data = {
        'weight_net': 25000.0,
        'ticket_number': 'TICKET-123',
        'guide_number': 'GUIDE-456',
        'quality_ph': 7.2,
        'quality_humidity': 60.5
    }
    
    dispatch_service.close_trip(load_id, close_data)
    
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Delivered', f"Expected 'Delivered', got '{load.status}'"
    assert load.weight_net == 25000.0
    assert load.ticket_number == 'TICKET-123'
    assert load.quality_ph == 7.2
    
    print(f"   ✅ Status is '{load.status}'")
    print("   ✅ Trip Closed Successfully with Data.")
    
    # Cleanup (Optional)
    print("🧹 Cleaning up...")
    # load_repo.delete(load_id) 
    
    print("🎉 Driver Flow Verification Successful!")

if __name__ == "__main__":
    verify_driver_flow()

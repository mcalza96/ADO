import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from services.operations.disposal_execution import DisposalExecutionService
from models.operations.load import Load

def verify_tto03():
    print("🚀 Starting TTO-03 Verification...")
    
    db_manager = DatabaseManager()
    load_repo = LoadRepository(db_manager)
    service = DisposalExecutionService(db_manager)
    
    # 1. Create a dummy load in 'Dispatched' status
    print("1️⃣ Creating dummy load...")
    dummy_load = Load(
        id=None,
        origin_facility_id=1,
        status='Dispatched',
        scheduled_date=datetime.now(),
        dispatch_time=datetime.now(),
        guide_number="TEST-GUIDE-001",
        weight_net=20000
    )
    
    created_load = load_repo.add(dummy_load)
    print(f"   ✅ Load created with ID: {created_load.id}")
    
    # 2. Execute TTO-03 Reception
    print("2️⃣ Executing TTO-03 Reception...")
    weight_gross = 25000.0
    ph = 7.5
    humidity = 80.0
    observation = "Test Observation"
    
    updated_load = service.register_reception_quality(
        load_id=created_load.id,
        weight=weight_gross,
        ph=ph,
        humidity=humidity,
        observation=observation
    )
    
    # 3. Verify Results
    print("3️⃣ Verifying results...")
    
    assert updated_load.status == 'Arrived', f"Expected status 'Arrived', got '{updated_load.status}'"
    assert updated_load.weight_gross_reception == weight_gross, f"Expected weight {weight_gross}, got {updated_load.weight_gross_reception}"
    assert updated_load.quality_ph == ph, f"Expected pH {ph}, got {updated_load.quality_ph}"
    assert updated_load.quality_humidity == humidity, f"Expected humidity {humidity}, got {updated_load.quality_humidity}"
    assert updated_load.reception_observations == observation, f"Expected observation '{observation}', got '{updated_load.reception_observations}'"
    
    print("   ✅ Status is 'Arrived'")
    print("   ✅ Fields updated correctly")
    
    # Cleanup
    print("🧹 Cleaning up...")
    # In a real test environment we would rollback, but here we might leave it or delete it.
    # For now, let's just print success.
    
    print("🎉 TTO-03 Verification Successful!")

if __name__ == "__main__":
    verify_tto03()

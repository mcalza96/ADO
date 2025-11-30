import sys
import os
import datetime

# Add project root to path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from services.operations.disposal_execution import DisposalExecutionService
from services.operations.treatment_reception import TreatmentReceptionService
from models.operations.load import Load
from repositories.load_repository import LoadRepository

def test_connection():
    db_path = "/tmp/test_trip_closing.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    db_manager = DatabaseManager(db_path)
    
    # Initialize schema
    with db_manager as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT,
                destination_site_id INTEGER,
                destination_treatment_plant_id INTEGER,
                arrival_time TIMESTAMP,
                weight_net REAL,
                created_at TIMESTAMP,
                scheduled_date DATE,
                origin_facility_id INTEGER,
                vehicle_id INTEGER,
                dispatch_time TIMESTAMP,
                guide_number TEXT,
                ticket_number TEXT,
                driver_id INTEGER,
                batch_id TEXT,
                weight_gross_reception REAL,
                reception_observations TEXT,
                reception_time TIMESTAMP,
                discharge_time TIMESTAMP,
                quality_ph REAL,
                quality_humidity REAL,
                updated_at TIMESTAMP,
                sync_status TEXT DEFAULT 'PENDING',
                last_updated_local TIMESTAMP
            )
        """)
    
    load_repo = LoadRepository(db_manager)
    disposal_service = DisposalExecutionService(db_manager)
    treatment_service = TreatmentReceptionService(db_manager)
    
    # 1. Test Disposal Connection
    print("Testing Disposal Connection...")
    load_disposal = Load(
        id=1,
        status='Delivered',
        destination_site_id=101,
        destination_treatment_plant_id=None,
        arrival_time=datetime.datetime.now(),
        weight_net=25000.0
    )
    load_repo.add(load_disposal)
    
    pending_disposal = disposal_service.get_pending_disposal_loads(101)
    if len(pending_disposal) == 1 and pending_disposal[0].id == 1:
        print("✅ Disposal Service correctly retrieved Delivered load.")
    else:
        print(f"❌ Disposal Service failed. Found: {len(pending_disposal)}")
        
    # 2. Test Treatment Connection
    print("\nTesting Treatment Connection...")
    load_treatment = Load(
        id=2,
        status='Delivered',
        destination_site_id=None,
        destination_treatment_plant_id=202,
        arrival_time=datetime.datetime.now(),
        weight_net=20000.0
    )
    load_repo.add(load_treatment)
    
    pending_treatment = treatment_service.get_pending_reception_loads(202)
    if len(pending_treatment) == 1 and pending_treatment[0].id == 2:
        print("✅ Treatment Service correctly retrieved Delivered load.")
    else:
        print(f"❌ Treatment Service failed. Found: {len(pending_treatment)}")

if __name__ == "__main__":
    test_connection()

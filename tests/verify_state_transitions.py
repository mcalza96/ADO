import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from models.operations.load import Load
from services.operations.logistics_service import LogisticsService
from services.operations.dispatch_service import DispatchService
from services.operations.disposal_execution import DisposalExecutionService
from domain.exceptions import TransitionException

def test_state_transitions():
    print("Starting State Transition Verification...")
    
    # Mock Dependencies
    mock_db = MagicMock()
    mock_compliance = MagicMock()
    mock_batch_service = MagicMock()
    
    # Instantiate Services
    logistics_service = LogisticsService(mock_db, mock_compliance)
    dispatch_service = DispatchService(mock_db, mock_batch_service)
    disposal_service = DisposalExecutionService(mock_db)
    
    # Mock Repository methods
    # We need to mock the repository inside the services. 
    # Since services instantiate LoadRepository internally, we need to mock that or the db_manager.
    # A cleaner way for this script is to monkeypatch the LoadRepository on the service instances
    # or mock the methods directly if they were injected. 
    # Since they are created in __init__, we can replace them.
    
    mock_repo = MagicMock()
    logistics_service.load_repo = mock_repo
    dispatch_service.load_repo = mock_repo
    disposal_service.load_repo = mock_repo
    
    # 1. Create Initial Load
    load = Load(id=1, status='Requested', requested_date=datetime.now())
    mock_repo.get_by_id.return_value = load
    mock_repo.update.return_value = True
    
    print(f"[1] Initial Status: {load.status}")
    
    # 2. Schedule Load (Requested -> Scheduled)
    print("\nTesting: Requested -> Scheduled")
    logistics_service.schedule_load(
        load_id=1, driver_id=101, vehicle_id=201, scheduled_date=datetime.now(), site_id=501
    )
    assert load.status == 'Scheduled', f"Failed: Status is {load.status}"
    assert load.sync_status == 'PENDING', "Failed: sync_status not PENDING"
    print("SUCCESS: Scheduled")
    
    # 3. Dispatch Load (Scheduled -> In Transit)
    print("\nTesting: Scheduled -> In Transit")
    dispatch_service.register_dispatch(
        load_id=1, ticket="T-123", gross=30000, tare=15000
    )
    assert load.status == 'In Transit', f"Failed: Status is {load.status}"
    assert load.sync_status == 'PENDING', "Failed: sync_status not PENDING"
    print("SUCCESS: In Transit")
    
    # 4. Register Arrival (In Transit -> PendingDisposal)
    print("\nTesting: In Transit -> PendingDisposal")
    disposal_service.register_arrival(load_id=1)
    assert load.status == 'PendingDisposal', f"Failed: Status is {load.status}"
    assert load.sync_status == 'PENDING', "Failed: sync_status not PENDING"
    print("SUCCESS: PendingDisposal")
    
    # 5. Execute Disposal (PendingDisposal -> Disposed)
    print("\nTesting: PendingDisposal -> Disposed")
    disposal_service.execute_disposal(load_id=1, coordinates="10.0, -20.0")
    assert load.status == 'Disposed', f"Failed: Status is {load.status}"
    assert load.sync_status == 'PENDING', "Failed: sync_status not PENDING"
    print("SUCCESS: Disposed")
    
    print("\nAll Happy Path transitions verified!")

def test_invalid_transitions():
    print("\nStarting Invalid Transition Verification...")
    
    mock_db = MagicMock()
    mock_compliance = MagicMock()
    logistics_service = LogisticsService(mock_db, mock_compliance)
    mock_repo = MagicMock()
    logistics_service.load_repo = mock_repo
    
    # Case: Try to schedule a load that is already Disposed
    load = Load(id=2, status='Disposed')
    mock_repo.get_by_id.return_value = load
    
    print("Testing: Disposed -> Scheduled (Should Fail)")
    try:
        logistics_service.schedule_load(
            load_id=2, driver_id=101, vehicle_id=201, scheduled_date=datetime.now(), site_id=501
        )
        print("FAILED: Should have raised TransitionException")
    except TransitionException as e:
        print(f"SUCCESS: Caught expected exception: {e}")
    except Exception as e:
        print(f"FAILED: Caught unexpected exception: {type(e)}")

if __name__ == "__main__":
    test_state_transitions()
    test_invalid_transitions()

from typing import List, Optional, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load
from services.operations.scheduling import SchedulingService
from services.operations.dispatching import DispatchService
from services.operations.reception import ReceptionService

class OperationsService:
    """
    Facade for Operations Module.
    Delegates to specialized services for state transitions.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = BaseRepository(db_manager, Load, "loads")
        
        # Sub-services
        self.scheduler = SchedulingService(db_manager)
        self.dispatcher = DispatchService(db_manager)
        self.receiver = ReceptionService(db_manager)

    def get_all_loads(self) -> List[Load]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loads ORDER BY scheduled_date DESC")
            rows = cursor.fetchall()
            return [Load(**dict(row)) for row in rows]
            
    def get_loads_by_status(self, status: str) -> List[Load]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loads WHERE status = ? ORDER BY created_at DESC", (status,))
            rows = cursor.fetchall()
            return [Load(**dict(row)) for row in rows]

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        return self.load_repo.get_by_id(load_id)

    # --- 1. REQUEST PHASE ---
    def create_request(self, facility_id: int, requested_date: datetime, user_id: Optional[int] = None) -> Load:
        """
        Creates a new Load Request.
        Only Facility is known. Status -> 'Requested'.
        """
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            status='Requested',
            created_by_user_id=user_id,
            created_at=datetime.now(),
            requested_date=requested_date,
            scheduled_date=None
        )
        return self.load_repo.add(load)

    # --- 2. PLANNING PHASE ---
    def assign_resources(self, load_id: int, driver_id: int, vehicle_id: int, site_id: int, scheduled_date: datetime) -> bool:
        """
        Assigns Driver, Vehicle, and Destination to a Requested Load.
        Status -> 'Scheduled'.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.destination_site_id = site_id
        load.scheduled_date = scheduled_date
        load.status = 'Scheduled'
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    # --- 3. EXECUTION PHASE ---
    def finalize_load(self, load_id: int, guide_number: str, ticket_number: str, weight_net: float) -> bool:
        """
        Finalizes the load with execution details.
        Status -> 'Delivered' (or 'Completed').
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        load.guide_number = guide_number
        load.ticket_number = ticket_number
        load.weight_net = weight_net
        # Assuming Gross/Tare are not strictly required if we trust the Net from the ticket
        # But we can set them if provided, or leave them as None
        
        load.status = 'Delivered'
        load.dispatch_time = datetime.now() # Or passed as arg
        load.arrival_time = datetime.now()
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    # --- LEGACY / UTILS ---
    def update_load_status(self, load_id: int, status: str, **kwargs) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if load:
            load.status = status
            return self.load_repo.update(load)
        return False

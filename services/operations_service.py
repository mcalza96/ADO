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

    def get_loads_by_facility(self, facility_id: int) -> List[Load]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loads WHERE origin_facility_id = ? ORDER BY scheduled_date DESC", (facility_id,))
            rows = cursor.fetchall()
            return [Load(**dict(row)) for row in rows]

    # --- 1. REQUEST PHASE ---
    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None) -> Load:
        """
        Creates a new Load Request.
        Can be from a Client Facility OR a Treatment Plant.
        """
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            origin_treatment_plant_id=plant_id,
            status='Requested',
            requested_date=requested_date,
            created_at=datetime.now()
        )
        return self.load_repo.add(load)

    # --- 2. PLANNING PHASE ---
    def assign_resources(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, container_quantity: Optional[int] = None) -> bool:
        """
        Assigns Driver, Vehicle, and Destination (Site OR Treatment Plant) to a Requested Load.
        Status -> 'Scheduled'.
        """
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.container_quantity = container_quantity
        
        # Hybrid Logistics Logic
        if treatment_plant_id:
            load.destination_treatment_plant_id = treatment_plant_id
            load.destination_site_id = None # Clear if switching
        else:
            load.destination_site_id = site_id
            load.destination_treatment_plant_id = None # Clear if switching
            
        load.scheduled_date = scheduled_date
        load.status = 'Scheduled'
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    # --- 3. EXECUTION PHASE ---
    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, 
                          container_1_id: Optional[int] = None, container_2_id: Optional[int] = None) -> bool:
        """
        Registers the dispatch of the load (Start of Trip).
        Links containers and batches if applicable.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            return False
            
        load.ticket_number = ticket
        load.weight_gross = gross
        load.weight_tare = tare
        load.weight_net = gross - tare
        load.dispatch_time = datetime.now()
        load.status = 'In Transit'
        
        # Link Containers & Batches (DS4 Logic)
        if container_1_id:
            load.container_1_id = container_1_id
            # Find active batch for this container
            from services.operations.treatment_batch_service import TreatmentBatchService
            batch_service = TreatmentBatchService(self.db_manager)
            batch1 = batch_service.get_active_batch_for_container(container_1_id)
            if batch1:
                load.batch_1_id = batch1.id
                batch_service.mark_as_dispatched(batch1.id)
                
        if container_2_id:
            load.container_2_id = container_2_id
            # Find active batch for this container
            from services.operations.treatment_batch_service import TreatmentBatchService
            batch_service = TreatmentBatchService(self.db_manager)
            batch2 = batch_service.get_active_batch_for_container(container_2_id)
            if batch2:
                load.batch_2_id = batch2.id
                batch_service.mark_as_dispatched(batch2.id)
        
        return self.load_repo.update(load)
        return self.dispatcher.register_dispatch(load_id, ticket, gross, tare, datetime.now(), container_1_id, container_2_id)

    def finalize_load(self, load_id: int, guide_number: str, ticket_number: str, weight_net: float) -> bool:
        """
        Finalizes the Transport phase.
        Status -> 'PendingDisposal' (if Site) OR 'PendingReception' (if Treatment Plant).
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        load.guide_number = guide_number
        load.ticket_number = ticket_number
        load.weight_net = weight_net
        
        # Determine Next State based on Destination
        if load.destination_treatment_plant_id:
            load.status = 'PendingReception'
        else:
            load.status = 'PendingDisposal'
            
        load.dispatch_time = datetime.now() # Or passed as arg
        load.arrival_time = datetime.now() # Assumed arrival at destination upon finalization
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    # --- LEGACY / UTILS ---
    def update_load_status(self, load_id: int, status: str, **kwargs) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if load:
            load.status = status
            return self.load_repo.update(load)
        return False

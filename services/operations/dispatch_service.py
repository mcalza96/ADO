from typing import Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from services.operations.treatment_batch_service import TreatmentBatchService
from domain.exceptions import TransitionException

class DispatchService:
    """
    Handles the Dispatch Execution phase.
    Responsibilities:
    - Registering Dispatch (Gate Out)
    - Linking Containers and Batches
    """
    def __init__(self, db_manager: DatabaseManager, batch_service: TreatmentBatchService):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.batch_service = batch_service

    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, 
                          container_1_id: Optional[int] = None, container_2_id: Optional[int] = None) -> bool:
        """
        Registers the dispatch of the load (Start of Trip).
        Links containers and batches if applicable.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            return False
            
        # State Transition Validation
        if load.status != 'Scheduled':
            raise TransitionException(f"Cannot dispatch load. Current status: {load.status}. Expected: 'Scheduled'.")
            
        load.ticket_number = ticket
        load.weight_gross = gross
        load.weight_tare = tare
        load.weight_net = gross - tare
        load.dispatch_time = datetime.now()
        load.status = 'In Transit'
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Link Containers & Batches (DS4 Logic)
        if container_1_id:
            load.container_1_id = container_1_id
            # Use injected batch_service
            batch1 = self.batch_service.get_active_batch_for_container(container_1_id)
            if batch1:
                load.batch_1_id = batch1.id
                self.batch_service.mark_as_dispatched(batch1.id)
                
        if container_2_id:
            load.container_2_id = container_2_id
            # Use injected batch_service
            batch2 = self.batch_service.get_active_batch_for_container(container_2_id)
            if batch2:
                load.batch_2_id = batch2.id
                self.batch_service.mark_as_dispatched(batch2.id)
        
        return self.load_repo.update(load)

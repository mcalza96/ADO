from typing import List, Optional, Any
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

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        return self.load_repo.get_by_id(load_id)

    def create_load(self, load: Load) -> Load:
        return self.scheduler.schedule_load(load)

    def update_load_status(self, load_id: int, status: str, **kwargs) -> bool:
        """
        Delegates to appropriate service based on status transition.
        """
        if status == 'InTransit':
            return self.dispatcher.register_dispatch(
                load_id, 
                kwargs.get('ticket_number'), 
                kwargs.get('weight_gross'), 
                kwargs.get('weight_tare'), 
                kwargs.get('dispatch_time')
            )
        elif status == 'Delivered':
            return self.receiver.register_arrival(
                load_id, 
                kwargs.get('arrival_time')
            )
        else:
            # Fallback for other status updates (e.g. Cancelled)
            # For now, simple update via repo if needed, or raise error
            # Implementing simple update for flexibility
            load = self.load_repo.get_by_id(load_id)
            if load:
                load.status = status
                return self.load_repo.update(load)
            return False

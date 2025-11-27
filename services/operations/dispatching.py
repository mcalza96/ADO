from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load

class DispatchService:
    def __init__(self, db_manager: DatabaseManager):
        self.load_repo = BaseRepository(db_manager, Load, "loads")

    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, dispatch_time: datetime) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        if load.status != 'Scheduled':
            raise ValueError("Load must be Scheduled to be dispatched")

        load.status = 'InTransit'
        load.ticket_number = ticket
        load.weight_gross = gross
        load.weight_tare = tare
        load.weight_net = gross - tare
        load.dispatch_time = dispatch_time
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

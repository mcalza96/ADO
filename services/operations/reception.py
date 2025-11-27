from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load

class ReceptionService:
    def __init__(self, db_manager: DatabaseManager):
        self.load_repo = BaseRepository(db_manager, Load, "loads")

    def register_arrival(self, load_id: int, arrival_time: datetime) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        if load.status != 'InTransit':
            raise ValueError("Load must be InTransit to be received")

        load.status = 'Delivered'
        load.arrival_time = arrival_time
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

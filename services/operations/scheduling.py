from typing import Optional
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load

class SchedulingService:
    def __init__(self, db_manager: DatabaseManager):
        self.load_repo = BaseRepository(db_manager, Load, "loads")

    def schedule_load(self, load: Load) -> Load:
        # Business logic: Validate schedule date, check driver availability, etc.
        load.status = 'Scheduled'
        return self.load_repo.add(load)

from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from domain.logistics.entities.load import Load

class TreatmentReceptionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        from domain.logistics.repositories.load_repository import LoadRepository
        self.load_repo = LoadRepository(db_manager)

    def get_pending_reception_loads(self, plant_id: int) -> List[Load]:
        """Loads that are 'Delivered' (Closed by Driver) at the Treatment Plant."""
        return self.load_repo.get_delivered_by_destination_type('TreatmentPlant', plant_id)

    def execute_reception(self, load_id: int, reception_time: datetime, discharge_time: datetime, ph: float, humidity: float) -> Load:
        """Transition from Delivered -> Treated (or Received)"""
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'Delivered':
            raise ValueError(f"Load must be Delivered to execute reception. Current: {load.status}")
            
        load.status = 'Treated' # Or 'ReceivedAtPlant'
        load.reception_time = reception_time
        load.discharge_time = discharge_time
        load.quality_ph = ph
        load.quality_humidity = humidity
        load.updated_at = datetime.now()
            
        return self.load_repo.update(load)

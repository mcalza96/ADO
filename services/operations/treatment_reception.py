from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load

class TreatmentReceptionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = BaseRepository(db_manager, Load, "loads")

    def get_pending_reception_loads(self, plant_id: int) -> List[Load]:
        """Loads that are PendingReception (Unloaded by Transport) at the Treatment Plant."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loads WHERE destination_treatment_plant_id = ? AND status = 'PendingReception'", (plant_id,))
            rows = cursor.fetchall()
            return [Load(**dict(row)) for row in rows]

    def execute_reception(self, load_id: int, reception_time: datetime, discharge_time: datetime, ph: float, humidity: float) -> Load:
        """Transition from PendingReception -> Treated (or Received)"""
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'PendingReception':
            raise ValueError(f"Load must be PendingReception to execute reception. Current: {load.status}")
            
        load.status = 'Treated' # Or 'ReceivedAtPlant'
        load.reception_time = reception_time
        load.discharge_time = discharge_time
        load.quality_ph = ph
        load.quality_humidity = humidity
        load.updated_at = datetime.now()
            
        return self.load_repo.update(load)

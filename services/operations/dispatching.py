from typing import Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load
from services.operations.treatment_batch_service import TreatmentBatchService

class DispatchService:
    def __init__(self, db_manager: DatabaseManager):
        self.load_repo = BaseRepository(db_manager, Load, "loads")
        self.batch_service = TreatmentBatchService(db_manager)

    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, dispatch_time: datetime, 
                          container_1_id: Optional[int] = None, container_2_id: Optional[int] = None) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        if load.status not in ['Scheduled', 'Requested']:
            raise ValueError(f"Load must be Scheduled or Requested to be dispatched. Current status: {load.status}")

        load.status = 'InTransit'
        load.ticket_number = ticket
        load.weight_gross = gross
        load.weight_tare = tare
        load.weight_net = gross - tare
        load.dispatch_time = dispatch_time
        
        # Link Containers and Batches
        if container_1_id:
            load.container_1_id = container_1_id
            batch_1 = self.batch_service.get_ready_batch_by_container(container_1_id)
            if batch_1:
                load.treatment_batch_1_id = batch_1.id
                # Link Quality Data (Taking from first batch as primary)
                load.quality_ph = batch_1.ph_24h if batch_1.ph_24h is not None else (batch_1.ph_2h if batch_1.ph_2h is not None else batch_1.ph_0h)
                load.quality_humidity = batch_1.humidity
                self.batch_service.mark_as_dispatched(batch_1.id)
            else:
                print(f"Warning: No READY batch found for container {container_1_id}")

        if container_2_id:
            load.container_2_id = container_2_id
            batch_2 = self.batch_service.get_ready_batch_by_container(container_2_id)
            if batch_2:
                load.treatment_batch_2_id = batch_2.id
                if load.quality_ph is None:
                    load.quality_ph = batch_2.ph_24h if batch_2.ph_24h is not None else (batch_2.ph_2h if batch_2.ph_2h is not None else batch_2.ph_0h)
                    load.quality_humidity = batch_2.humidity
                self.batch_service.mark_as_dispatched(batch_2.id)

        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

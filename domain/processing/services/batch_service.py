from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from domain.processing.entities.treatment_batch import TreatmentBatch
from domain.logistics.entities.container import Container

class TreatmentBatchService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repo = BaseRepository(db_manager, TreatmentBatch, "treatment_batches")
        self.container_repo = BaseRepository(db_manager, Container, "containers")

    def create_batch(self, facility_id: int, container_id: int, fill_time: datetime, ph_0h: float, humidity: float) -> TreatmentBatch:
        batch = TreatmentBatch(
            id=None,
            facility_id=facility_id,
            container_id=container_id,
            fill_time=fill_time,
            ph_0h=ph_0h,
            humidity=humidity,
            status='READY', # Immediately ready for dispatch
            created_at=datetime.now()
        )
        saved_batch = self.repo.add(batch)
        
        # Update Container Status
        # Update Container Status
        container = self.container_repo.get_by_id(container_id)
        if container:
            container.status = 'IN_USE'
            self.container_repo.update(container)
        
        return saved_batch

    def update_ph_2h(self, batch_id: int, ph: float):
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE treatment_batches SET ph_2h = ? WHERE id = ?", (ph, batch_id))
            conn.commit()

    def update_ph_24h(self, batch_id: int, ph: Optional[float]):
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE treatment_batches SET ph_24h = ? WHERE id = ?", (ph, batch_id))
            conn.commit()

    def get_active_batches(self, facility_id: int) -> List[TreatmentBatch]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Now we fetch READY batches too because they are still "active" in terms of monitoring until dispatched
            # But for simplicity, let's just fetch everything that hasn't been dispatched (status != DISPATCHED)
            # Assuming 'READY' means ready for pickup but still in plant.
            cursor.execute("SELECT * FROM treatment_batches WHERE facility_id = ? AND status = 'READY' ORDER BY fill_time DESC", (facility_id,))
            rows = cursor.fetchall()
            return [TreatmentBatch(**dict(row)) for row in rows]
    
    def get_batches_by_facility(self, facility_id: int) -> List[TreatmentBatch]:
        """Returns empty list - TreatmentBatches are not used in current implementation.
        Use TreatmentService.get_batches_by_facility() for production batches instead."""
        return []
            
    def get_ready_batches(self, plant_id: int) -> List[TreatmentBatch]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM treatment_batches WHERE plant_id = ? AND status = 'READY' ORDER BY fill_time ASC", (plant_id,))
            rows = cursor.fetchall()
            return [TreatmentBatch(**dict(row)) for row in rows]

    def get_active_batch_for_container(self, container_id: int) -> Optional[TreatmentBatch]:
        """
        Finds the current active batch (READY or MONITORING) for a specific container.
        Used during Dispatch to link the Load to the Batch.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # We look for batches that are NOT dispatched yet.
            cursor.execute("SELECT * FROM treatment_batches WHERE container_id = ? AND status IN ('READY', 'MONITORING') ORDER BY created_at DESC LIMIT 1", (container_id,))
            row = cursor.fetchone()
            if row:
                return TreatmentBatch(**dict(row))
            return None

    def mark_as_dispatched(self, batch_id: int):
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE treatment_batches SET status = 'DISPATCHED' WHERE id = ?", (batch_id,))
            conn.commit()

    def get_ready_batch_by_container(self, container_id: int) -> Optional[TreatmentBatch]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM treatment_batches WHERE container_id = ? AND status = 'READY'", (container_id,))
            row = cursor.fetchone()
            if row:
                return TreatmentBatch(**dict(row))
            return None

    def mark_as_dispatched(self, batch_id: int):
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE treatment_batches SET status = 'DISPATCHED' WHERE id = ?", (batch_id,))
            conn.commit()


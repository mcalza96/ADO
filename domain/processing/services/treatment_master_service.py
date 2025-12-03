from typing import List
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from domain.processing.entities.treatment_type import Batch, LabResult

class TreatmentService:
    def __init__(self, db_manager: DatabaseManager):
        self.batch_repo = BaseRepository(db_manager, Batch, "batches")
        self.lab_repo = BaseRepository(db_manager, LabResult, "lab_results")
        self.db_manager = db_manager

    # --- Batches ---
    def get_batches_by_facility(self, facility_id: int) -> List[Batch]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM batches WHERE facility_id = ? ORDER BY production_date DESC", (facility_id,))
            rows = cursor.fetchall()
            return [Batch(**dict(row)) for row in rows]

    def create_batch(self, batch: Batch) -> Batch:
        return self.batch_repo.add(batch)
    
    def create_daily_batch(self, facility_id: int, batch_code: str, production_date, 
                          initial_tonnage: float, class_type: str, sludge_type: str = None) -> Batch:
        """Creates a new daily batch."""
        batch = Batch(
            id=None,
            facility_id=facility_id,
            batch_code=batch_code,
            production_date=production_date,
            initial_tonnage=initial_tonnage,
            current_tonnage=initial_tonnage,
            class_type=class_type,
            sludge_type=sludge_type,
            status='Available',
            created_at=datetime.now()
        )
        return self.batch_repo.add(batch)

    # --- Lab Results ---
    def add_lab_result(self, result: LabResult) -> LabResult:
        return self.lab_repo.add(result)
    
    def get_lab_results_by_batch(self, batch_id: int) -> List[LabResult]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lab_results WHERE batch_id = ?", (batch_id,))
            rows = cursor.fetchall()
            return [LabResult(**dict(row)) for row in rows]

from typing import List
from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.processing.entities.treatment_type import Batch, LabResult

class TreatmentRepository:
    """
    Repository for Treatment module entities (Batches, LabResults).
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.batch_repo = BaseRepository(db_manager, Batch, "batches")
        self.lab_repo = BaseRepository(db_manager, LabResult, "lab_results")

    def get_batches_by_facility(self, facility_id: int) -> List[Batch]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM batches WHERE facility_id = ? ORDER BY production_date DESC", (facility_id,))
            rows = cursor.fetchall()
            return [Batch(**dict(row)) for row in rows]

    def get_lab_results_by_batch(self, batch_id: int) -> List[LabResult]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lab_results WHERE batch_id = ?", (batch_id,))
            rows = cursor.fetchall()
            return [LabResult(**dict(row)) for row in rows]
            
    def add_batch(self, batch: Batch) -> Batch:
        return self.batch_repo.add(batch)
        
    def add_lab_result(self, result: LabResult) -> LabResult:
        return self.lab_repo.add(result)

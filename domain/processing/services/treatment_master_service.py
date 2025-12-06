from typing import List
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager
from domain.processing.entities.treatment_type import Batch, LabResult
from domain.processing.repositories.treatment_repository import TreatmentRepository

class TreatmentService:
    def __init__(self, db_manager: DatabaseManager):
        self.repository = TreatmentRepository(db_manager)

    # --- Batches ---
    def get_batches_by_facility(self, facility_id: int) -> List[Batch]:
        return self.repository.get_batches_by_facility(facility_id)

    def create_batch(self, batch: Batch) -> Batch:
        return self.repository.add_batch(batch)
    
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
        return self.repository.add_batch(batch)

    # --- Lab Results ---
    def add_lab_result(self, result: LabResult) -> LabResult:
        return self.repository.add_lab_result(result)
    
    def get_lab_results_by_batch(self, batch_id: int) -> List[LabResult]:
        return self.repository.get_lab_results_by_batch(batch_id)

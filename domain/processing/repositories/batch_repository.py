from typing import List, Optional
from database.repository import BaseRepository
from domain.processing.entities.treatment_type import Batch
from database.db_manager import DatabaseManager

class BatchRepository(BaseRepository[Batch]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Batch, "batches")

    def get_by_facility(self, facility_id: int) -> List[Batch]:
        """
        Returns all batches for a specific facility, ordered by production_date DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE facility_id = ? ORDER BY production_date DESC",
                (facility_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_available_batches(self, facility_id: Optional[int] = None) -> List[Batch]:
        """
        Returns batches with status='Available' and current_tonnage > 0.
        Optionally filtered by facility_id.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            if facility_id:
                cursor.execute(
                    f"SELECT * FROM {self.table_name} WHERE facility_id = ? AND status = 'Available' AND current_tonnage > 0 ORDER BY production_date ASC",
                    (facility_id,)
                )
            else:
                cursor.execute(
                    f"SELECT * FROM {self.table_name} WHERE status = 'Available' AND current_tonnage > 0 ORDER BY production_date ASC"
                )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_batch_code(self, batch_code: str) -> Optional[Batch]:
        """
        Returns a batch by its unique batch_code.
        Used for validation of uniqueness.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE batch_code = ?", (batch_code,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None

    def update_current_tonnage(self, batch_id: int, amount: float) -> bool:
        """
        Critical method: Updates current_tonnage by subtracting (or adding if negative) the amount.
        Used when dispatching trucks (subtract) or receiving returns (add).
        
        Args:
            batch_id: ID of the batch
            amount: Amount to subtract from current_tonnage (positive to reduce, negative to increase)
        
        Returns:
            True if update successful, False otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Get current tonnage first to validate
            cursor.execute(f"SELECT current_tonnage FROM {self.table_name} WHERE id = ?", (batch_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            current = row['current_tonnage'] or 0
            new_tonnage = current - amount
            
            # Prevent negative tonnage
            if new_tonnage < 0:
                raise ValueError(f"Insufficient stock. Available: {current} kg, Requested: {amount} kg")
            
            cursor.execute(
                f"UPDATE {self.table_name} SET current_tonnage = ? WHERE id = ?",
                (new_tonnage, batch_id)
            )
            
            # Auto-update status to Depleted if tonnage reaches zero
            if new_tonnage == 0:
                cursor.execute(
                    f"UPDATE {self.table_name} SET status = 'Depleted' WHERE id = ?",
                    (batch_id,)
                )
            
            return cursor.rowcount > 0

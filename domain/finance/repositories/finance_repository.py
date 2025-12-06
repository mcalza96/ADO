from typing import Optional, List
from infrastructure.persistence.generic_repository import BaseRepository
from domain.finance.entities.finance_entities import RateSheet, CostRecord
from infrastructure.persistence.database_manager import DatabaseManager

class RateSheetRepository(BaseRepository[RateSheet]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, RateSheet, "rate_sheets")
    
    def get_rate(self, activity_type: str, client_id: Optional[int] = None) -> Optional[RateSheet]:
        """
        Busca la mejor tarifa aplicable.
        Prioridad: Tarifa específica de cliente > Tarifa base (client_id IS NULL).
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Intentar buscar específica
            if client_id:
                cursor.execute(
                    f"SELECT * FROM {self.table_name} WHERE activity_type = ? AND client_id = ? ORDER BY id DESC LIMIT 1",
                    (activity_type, client_id)
                )
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_model(dict(row))
            
            # Buscar default
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE activity_type = ? AND client_id IS NULL ORDER BY id DESC LIMIT 1",
                (activity_type,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(dict(row)) if row else None

class CostRecordRepository(BaseRepository[CostRecord]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, CostRecord, "cost_records")

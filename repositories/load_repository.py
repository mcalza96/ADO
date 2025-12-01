from typing import List
from datetime import datetime
from database.repository import BaseRepository
from models.operations.load import Load
from database.db_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def get_next_manifest_sequence(self) -> int:
        """
        Returns the next sequence number for the current year.
        Counts how many loads were created this year and adds 1.
        """
        current_year = datetime.now().year
        start_date = f"{current_year}-01-01 00:00:00"
        end_date = f"{current_year}-12-31 23:59:59"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM {self.table_name} WHERE created_at BETWEEN ? AND ?",
                (start_date, end_date)
            )
            count = cursor.fetchone()[0]
            return count + 1

    def get_active_loads(self) -> List[Load]:
        """
        Returns all loads that are NOT 'COMPLETED' or 'CANCELLED'.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status NOT IN ('COMPLETED', 'CANCELLED') ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_status(self, status: str) -> List[Load]:
        """
        Returns loads filtered by status, ordered by created_at DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC", (status,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

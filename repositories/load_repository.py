from typing import List
from database.repository import BaseRepository
from models.operations.load import Load
from database.db_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def get_all_ordered_by_date(self) -> List[Load]:
        """
        Returns all loads ordered by scheduled_date DESC.
        """
        return self.get_all(order_by="scheduled_date DESC")

    def get_by_status(self, status: str) -> List[Load]:
        """
        Returns loads filtered by status, ordered by created_at DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC", (status,))
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]

    def get_by_origin_facility(self, facility_id: int) -> List[Load]:
        """
        Returns loads filtered by origin_facility_id, ordered by scheduled_date DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE origin_facility_id = ? ORDER BY scheduled_date DESC", (facility_id,))
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]

    def get_by_destination_and_status(self, destination_site_id: int, status: str) -> List[Load]:
        """
        Returns loads filtered by destination_site_id and status.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE destination_site_id = ? AND status = ?", (destination_site_id, status))
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]

from typing import List, Optional
from database.repository import BaseRepository
from models.masters.driver import Driver
from database.db_manager import DatabaseManager


class DriverRepository(BaseRepository[Driver]):
    """
    Repository for Driver entity.
    Handles all data access operations for transport drivers.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Driver, "drivers")
    
    def get_by_contractor(self, contractor_id: int) -> List[Driver]:
        """
        Get all active drivers for a specific contractor with contractor name.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT d.*, c.name as contractor_name 
                FROM {self.table_name} d
                JOIN contractors c ON d.contractor_id = c.id
                WHERE d.contractor_id = ? AND d.is_active = 1 
                ORDER BY d.name
                """,
                (contractor_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_by_rut(self, rut: str) -> Optional[Driver]:
        """
        Get a driver by RUT.
        Useful for validating duplicates.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE rut = ?",
                (rut,)
            )
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None
            
    def get_all_active(self) -> List[Driver]:
        """
        Get all active drivers across all contractors with contractor name.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT d.*, c.name as contractor_name 
                FROM {self.table_name} d
                JOIN contractors c ON d.contractor_id = c.id
                WHERE d.is_active = 1 
                ORDER BY d.name
                """
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

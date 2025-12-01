from typing import List, Optional
from database.repository import BaseRepository
from models.masters.vehicle import Vehicle
from database.db_manager import DatabaseManager


class VehicleRepository(BaseRepository[Vehicle]):
    """
    Repository for Vehicle entity.
    Handles all data access operations for transport vehicles.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Vehicle, "vehicles")
    
    def get_by_contractor(self, contractor_id: int) -> List[Vehicle]:
        """
        Get all active vehicles for a specific contractor with contractor name.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT v.*, c.name as contractor_name 
                FROM {self.table_name} v
                JOIN contractors c ON v.contractor_id = c.id
                WHERE v.contractor_id = ? AND v.is_active = 1 
                ORDER BY v.license_plate
                """,
                (contractor_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_by_license_plate(self, license_plate: str) -> Optional[Vehicle]:
        """
        Get a vehicle by its license plate.
        Useful for validating duplicate plates.
        
        Args:
            license_plate: Vehicle license plate
            
        Returns:
            Vehicle if found, None otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE license_plate = ?",
                (license_plate,)
            )
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None
    
    def get_all_active(self) -> List[Vehicle]:
        """
        Get all active vehicles across all contractors with contractor name.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT v.*, c.name as contractor_name 
                FROM {self.table_name} v
                JOIN contractors c ON v.contractor_id = c.id
                WHERE v.is_active = 1 
                ORDER BY v.license_plate
                """
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

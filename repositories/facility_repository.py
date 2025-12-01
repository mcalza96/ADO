from typing import List, Optional
from database.repository import BaseRepository
from models.masters.location import Facility
from database.db_manager import DatabaseManager


class FacilityRepository(BaseRepository[Facility]):
    """
    Repository for Facility entity (Treatment Plants).
    Handles all data access operations for wastewater treatment facilities.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Facility, "facilities")
    
    def get_by_client(self, client_id: int) -> List[Facility]:
        """
        Get all active facilities for a specific client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            List of active facilities belonging to the client
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE client_id = ? AND is_active = 1 ORDER BY name",
                (client_id,)
            )
            rows = cursor.fetchall()
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_all_active(self) -> List[Facility]:
        """
        Get all active facilities across all clients.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE is_active = 1 ORDER BY name"
            )
            rows = cursor.fetchall()
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def update_allowed_vehicle_types(self, facility_id: int, allowed_types: str) -> bool:
        """
        Update the allowed vehicle types for a facility.
        
        Args:
            facility_id: ID of the facility
            allowed_types: Comma-separated string of allowed vehicle types (e.g., "BATEA,AMPLIROLL")
            
        Returns:
            True if update was successful, False otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET allowed_vehicle_types = ? WHERE id = ?",
                (allowed_types, facility_id)
            )
            return cursor.rowcount > 0

from typing import List, Optional
from database.repository import BaseRepository
from models.masters.treatment_plant import TreatmentPlant
from database.db_manager import DatabaseManager


class TreatmentPlantRepository(BaseRepository[TreatmentPlant]):
    """
    Repository for TreatmentPlant entity.
    Handles all data access operations for wastewater treatment plants.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, TreatmentPlant, "facilities")
    
    def get_by_client(self, client_id: int) -> List[TreatmentPlant]:
        """
        Get all active treatment plants for a specific client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            List of active treatment plants belonging to the client
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE client_id = ? AND is_active = 1 ORDER BY name",
                (client_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_client_id(self, client_id: int) -> List[TreatmentPlant]:
        """Alias for get_by_client to match service expectations."""
        return self.get_by_client(client_id)
    
    def get_all(self) -> List[TreatmentPlant]:
        """
        Get all active treatment plants.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Explicitly selecting columns to ensure client_id is included
            query = """
            SELECT id, client_id, name, address, latitude, longitude, 
                   authorization_resolution, allowed_vehicle_types, is_active 
            FROM facilities 
            WHERE is_active = 1
            ORDER BY name
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return [TreatmentPlant(**dict(row)) for row in rows]
    
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

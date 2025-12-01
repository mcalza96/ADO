from typing import List, Optional
import sqlite3
from database.db_manager import DatabaseManager
from repositories.facility_repository import FacilityRepository
from models.masters.location import Facility


class FacilityService:
    """
    Service layer for Facility (Treatment Plant) entity.
    Implements business logic and validation for wastewater treatment facilities.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repository = FacilityRepository(db_manager)

    def get_all_facilities(self, active_only: bool = True) -> List[Facility]:
        """
        Get all facilities, optionally filtered by active status.
        
        Args:
            active_only: If True, only return active facilities
            
        Returns:
            List of Facility objects
        """
        try:
            return self.repository.get_all(active_only=active_only, order_by="name")
        except sqlite3.Error as e:
            raise Exception(f"Error fetching facilities: {str(e)}")

    def get_facility_by_id(self, facility_id: int) -> Optional[Facility]:
        """
        Get a single facility by ID.
        
        Args:
            facility_id: Facility ID
            
        Returns:
            Facility object or None if not found
        """
        try:
            return self.repository.get_by_id(facility_id)
        except sqlite3.Error as e:
            raise Exception(f"Error fetching facility {facility_id}: {str(e)}")

    def get_by_client(self, client_id: int, active_only: bool = True) -> List[Facility]:
        """
        Get all facilities for a specific client.
        
        Args:
            client_id: Client ID
            active_only: If True, only return active facilities
            
        Returns:
            List of Facility objects
        """
        try:
            facilities = self.repository.get_by_client(client_id)
            if active_only:
                facilities = [f for f in facilities if f.is_active]
            return facilities
        except sqlite3.Error as e:
            raise Exception(f"Error fetching facilities for client {client_id}: {str(e)}")

    def save(self, facility: Facility) -> Facility:
        """
        Save a facility (create new or update existing).
        Intelligently decides between add() and update() based on ID.
        
        Args:
            facility: Facility object to save
            
        Returns:
            Saved Facility object with ID
            
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Business validation: Name is required
        if not facility.name or not facility.name.strip():
            raise ValueError("El nombre de la planta es obligatorio.")
        
        # Business validation: Client ID is required
        if not facility.client_id:
            raise ValueError("La planta debe estar asociada a un cliente.")
        
        # Note: The requirement mentioned default_mineralization_rate, but this field
        # doesn't exist in the current Facility model. This might be a field for
        # another entity or future enhancement. Skipping this validation for now.
        
        try:
            # Decide between create and update
            if facility.id is None:
                # Create new facility
                return self.repository.add(facility)
            else:
                # Update existing facility
                success = self.repository.update(facility)
                if not success:
                    raise Exception(f"No se pudo actualizar la planta con ID {facility.id}")
                return facility
        except sqlite3.Error as e:
            raise Exception(f"Error guardando planta: {str(e)}")

    def delete_facility(self, facility_id: int) -> bool:
        """
        Soft delete a facility (sets is_active = 0).
        
        Args:
            facility_id: Facility ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            return self.repository.delete(facility_id)
        except sqlite3.Error as e:
            raise Exception(f"Error eliminando planta {facility_id}: {str(e)}")

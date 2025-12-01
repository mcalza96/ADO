from typing import List, Optional
import sqlite3
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.contractor_repository import ContractorRepository
from models.masters.transport import Contractor


class ContractorService:
    """
    Service layer for Contractor entity.
    Implements business logic and validation for transport contractors.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repository = ContractorRepository(db_manager)

    def get_all_contractors(self, active_only: bool = True) -> List[Contractor]:
        """
        Get all contractors, optionally filtered by active status.
        
        Args:
            active_only: If True, only return active contractors
            
        Returns:
            List of Contractor objects
        """
        try:
            return self.repository.get_all(active_only=active_only, order_by="name")
        except sqlite3.Error as e:
            raise Exception(f"Error fetching contractors: {str(e)}")

    def get_contractor_by_id(self, contractor_id: int) -> Optional[Contractor]:
        """
        Get a single contractor by ID.
        
        Args:
            contractor_id: Contractor ID
            
        Returns:
            Contractor object or None if not found
        """
        try:
            return self.repository.get_by_id(contractor_id)
        except sqlite3.Error as e:
            raise Exception(f"Error fetching contractor {contractor_id}: {str(e)}")

    def validate_unique_rut(self, rut: str, exclude_id: Optional[int] = None) -> bool:
        """
        Validate that a RUT is unique (not already in use by another contractor).
        
        Args:
            rut: RUT to validate
            exclude_id: Contractor ID to exclude from validation (for updates)
            
        Returns:
            True if RUT is unique, False if already exists
        """
        if not rut:
            return True  # Empty RUT is allowed
        
        try:
            existing_contractor = self.repository.get_by_rut(rut)
            
            # RUT is unique if not found, or if it belongs to the contractor being updated
            if existing_contractor is None:
                return True
            
            if exclude_id and existing_contractor.id == exclude_id:
                return True
            
            return False
        except sqlite3.Error as e:
            raise Exception(f"Error validating RUT: {str(e)}")

    def save(self, contractor: Contractor) -> Contractor:
        """
        Save a contractor (create new or update existing).
        Intelligently decides between add() and update() based on ID.
        
        Args:
            contractor: Contractor object to save
            
        Returns:
            Saved Contractor object with ID
            
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Business validation: Validate unique RUT
        if contractor.rut:
            if not self.validate_unique_rut(contractor.rut, exclude_id=contractor.id):
                raise ValueError(f"El RUT '{contractor.rut}' ya está registrado para otro contratista.")
        
        # Business validation: Name is required
        if not contractor.name or not contractor.name.strip():
            raise ValueError("El nombre del contratista es obligatorio.")
        
        # Note: The requirement mentioned validating "formato de fecha de seguro"
        # (insurance date format), but the current Contractor model doesn't have
        # an insurance_date field. This might be a future enhancement or field
        # in a related entity. Skipping this validation for now.
        
        try:
            # Decide between create and update
            if contractor.id is None:
                # Create new contractor
                return self.repository.add(contractor)
            else:
                # Update existing contractor
                success = self.repository.update(contractor)
                if not success:
                    raise Exception(f"No se pudo actualizar el contratista con ID {contractor.id}")
                return contractor
        except sqlite3.Error as e:
            raise Exception(f"Error guardando contratista: {str(e)}")

    def delete_contractor(self, contractor_id: int) -> bool:
        """
        Soft delete a contractor (sets is_active = 0).
        
        Args:
            contractor_id: Contractor ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            return self.repository.delete(contractor_id)
        except sqlite3.Error as e:
            raise Exception(f"Error eliminando contratista {contractor_id}: {str(e)}")

from typing import List, Optional
import sqlite3
from database.db_manager import DatabaseManager
from repositories.client_repository import ClientRepository
from models.masters.client import Client


class ClientService:
    """
    Service layer for Client entity with business logic and validation.
    Implements the Service Pattern for client management.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repository = ClientRepository(db_manager)

    def get_all_clients(self, active_only: bool = True) -> List[Client]:
        """
        Get all clients, optionally filtered by active status.
        
        Args:
            active_only: If True, only return active clients
            
        Returns:
            List of Client objects
        """
        try:
            return self.repository.get_all(active_only=active_only, order_by="name")
        except sqlite3.Error as e:
            raise Exception(f"Error fetching clients: {str(e)}")

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """
        Get a single client by ID.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client object or None if not found
        """
        try:
            return self.repository.get_by_id(client_id)
        except sqlite3.Error as e:
            raise Exception(f"Error fetching client {client_id}: {str(e)}")

    def validate_unique_rut(self, rut: str, exclude_id: Optional[int] = None) -> bool:
        """
        Validate that a RUT is unique (not already in use by another client).
        
        Args:
            rut: RUT to validate
            exclude_id: Client ID to exclude from validation (for updates)
            
        Returns:
            True if RUT is unique, False if already exists
        """
        if not rut:
            return True  # Empty RUT is allowed
        
        try:
            existing_client = self.repository.get_by_rut(rut)
            
            # RUT is unique if not found, or if it belongs to the client being updated
            if existing_client is None:
                return True
            
            if exclude_id and existing_client.id == exclude_id:
                return True
            
            return False
        except sqlite3.Error as e:
            raise Exception(f"Error validating RUT: {str(e)}")

    def save(self, client: Client) -> Client:
        """
        Save a client (create new or update existing).
        Intelligently decides between add() and update() based on ID.
        
        Args:
            client: Client object to save
            
        Returns:
            Saved Client object with ID
            
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Business validation: Validate unique RUT
        if client.rut:
            if not self.validate_unique_rut(client.rut, exclude_id=client.id):
                raise ValueError(f"El RUT '{client.rut}' ya está registrado para otro cliente.")
        
        # Business validation: Name is required
        if not client.name or not client.name.strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        
        try:
            # Decide between create and update
            if client.id is None:
                # Create new client
                return self.repository.add(client)
            else:
                # Update existing client
                success = self.repository.update(client)
                if not success:
                    raise Exception(f"No se pudo actualizar el cliente con ID {client.id}")
                return client
        except sqlite3.Error as e:
            raise Exception(f"Error guardando cliente: {str(e)}")

    def delete_client(self, client_id: int) -> bool:
        """
        Soft delete a client (sets is_active = 0).
        
        Args:
            client_id: Client ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            return self.repository.delete(client_id)
        except sqlite3.Error as e:
            raise Exception(f"Error eliminando cliente {client_id}: {str(e)}")

    # Legacy methods for backward compatibility
    def create_client(self, client: Client) -> Client:
        """Legacy method - use save() instead."""
        return self.save(client)

    def update_client(self, client: Client) -> bool:
        """Legacy method - use save() instead."""
        try:
            self.save(client)
            return True
        except Exception:
            return False

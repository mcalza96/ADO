from typing import TypeVar, Generic, List, Optional, Any
from services.base_service import BaseService
from database.repository import BaseRepository

T = TypeVar("T")

class GenericCrudService(BaseService, Generic[T]):
    """
    Generic Service for CRUD operations.
    Replaces specific services that only pass calls to the repository.
    """
    def __init__(self, repository: BaseRepository[T]):
        # BaseService expects db_manager, but we might not need it if we have repo.
        # However, BaseService init is: self.db_manager = db_manager
        # We can pass repo.db_manager
        super().__init__(repository.db_manager)
        self.repo = repository

    def get_all(self, active_only: bool = True) -> List[T]:
        """
        Get all records.
        """
        return self.repo.get_all(active_only=active_only)

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get record by ID.
        """
        return self.repo.get_by_id(id)

    def save(self, entity: T) -> T:
        """
        Create or update a record.
        """
        # Simple logic: if has ID, update; else add.
        if getattr(entity, 'id', None):
            self.repo.update(entity)
            return entity
        else:
            return self.repo.add(entity)

    def delete(self, id: int) -> bool:
        """
        Delete a record.
        """
        return self.repo.delete(id)
        
    def get_by_attribute(self, attribute: str, value: Any) -> Optional[T]:
        """
        Get by specific attribute (e.g. rut, license_plate).
        """
        return self.repo.get_by_attribute(attribute, value)
    
    # Backward compatibility aliases for entity-specific methods
    def get_all_clients(self, active_only: bool = True) -> List[T]:
        """Alias for get_all() - for Client entities."""
        return self.get_all(active_only=active_only)
    
    def get_all_vehicles(self, active_only: bool = True) -> List[T]:
        """Alias for get_all() - for Vehicle entities."""
        return self.get_all(active_only=active_only)
    
    def get_all_contractors(self, active_only: bool = True) -> List[T]:
        """Alias for get_all() - for Contractor entities."""
        return self.get_all(active_only=active_only)
    
    def get_drivers_by_contractor(self, contractor_id: int) -> List[T]:
        """Get drivers filtered by contractor."""
        return self.repo.get_all_filtered(contractor_id=contractor_id, is_active=1)
    
    def get_vehicles_by_contractor(self, contractor_id: int) -> List[T]:
        """Get vehicles filtered by contractor."""
        return self.repo.get_all_filtered(contractor_id=contractor_id, is_active=1)
    
    def get_by_client(self, client_id: int) -> List[T]:
        """Get items filtered by client_id (for treatment plants)."""
        return self.repo.get_all_filtered(client_id=client_id, is_active=1)
    
    def get_available_containers(self, plant_id: int) -> List[T]:
        """Get available containers at a plant."""
        # Return containers with status 'Available' or similar
        # This is a simplified version - adjust based on your Container model
        all_containers = self.repo.get_all(active_only=True)
        return [c for c in all_containers if getattr(c, 'status', None) == 'Available']

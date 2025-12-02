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

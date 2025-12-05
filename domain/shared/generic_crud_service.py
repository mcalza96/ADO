from typing import TypeVar, Generic, List, Optional, Any
from domain.shared.base_service import BaseService
from domain.shared.enums import DisplayableEnum
from database.repository import BaseRepository

T = TypeVar("T")


# Campos conocidos que usan enums y sus clases correspondientes
ENUM_FIELD_VALIDATORS = {
    'type': 'domain.logistics.entities.vehicle.VehicleType',
    'asset_type': 'domain.logistics.entities.vehicle.AssetType',
    'status': 'domain.logistics.entities.load_status.LoadStatus',
}


def _validate_enum_field(field_name: str, value: Any) -> None:
    """
    Valida que un campo enum contenga un valor válido, no un display_name.
    
    Raises:
        ValueError: Si el valor parece ser un display_name en lugar de un valor de enum
    """
    if not value or not isinstance(value, str):
        return
    
    # Detectar patrones comunes de display_names (contienen paréntesis, espacios descriptivos)
    display_name_indicators = [
        '(' in value and ')' in value,  # "Batea (carga directa)"
        value != value.upper() and ' ' in value,  # "En Ruta" vs "EN_ROUTE"
    ]
    
    if any(display_name_indicators):
        # Podría ser un display_name - generar advertencia
        import warnings
        warnings.warn(
            f"El campo '{field_name}' contiene '{value}' que parece ser un display_name. "
            f"Los valores de enum deben ser en MAYÚSCULAS sin espacios (ej: 'BATEA', 'AMPLIROLL').",
            UserWarning
        )


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
        Includes validation for enum fields.
        """
        # Validar campos de enum antes de guardar
        self._validate_enum_fields(entity)
        
        # Simple logic: if has ID, update; else add.
        if getattr(entity, 'id', None):
            self.repo.update(entity)
            return entity
        else:
            return self.repo.add(entity)
    
    def _validate_enum_fields(self, entity: T) -> None:
        """Valida campos que deberían contener valores de enum."""
        for field_name in ['type', 'asset_type', 'status']:
            if hasattr(entity, field_name):
                value = getattr(entity, field_name)
                _validate_enum_field(field_name, value)

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
    
    # Container-specific aliases
    def get_all_containers(self, active_only: bool = True) -> List[T]:
        """Alias for get_all() - for Container entities."""
        return self.get_all(active_only=active_only)
    
    def get_container_by_id(self, container_id: int) -> Optional[T]:
        """Get container by ID."""
        return self.get_by_id(container_id)
    
    def get_by_contractor(self, contractor_id: int, active_only: bool = True) -> List[T]:
        """Get containers filtered by contractor."""
        is_active = 1 if active_only else None
        if is_active:
            return self.repo.get_all_filtered(contractor_id=contractor_id, is_active=is_active)
        return self.repo.get_all_filtered(contractor_id=contractor_id)
    
    def delete_container(self, container_id: int) -> bool:
        """Soft delete a container."""
        return self.delete(container_id)
    
    def get_available_containers(self, plant_id: int = None) -> List[T]:
        """Get available containers (status='Available')."""
        all_containers = self.repo.get_all(active_only=True)
        return [c for c in all_containers if getattr(c, 'status', None) == 'Available']


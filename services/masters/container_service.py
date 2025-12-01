from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.container_repository import ContainerRepository
from repositories.contractor_repository import ContractorRepository
from models.masters.container import Container


class ContainerService:
    """
    Service layer for Container entity.
    Implements business logic and validation for Roll-off containers.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repository = ContainerRepository(db_manager)
        self.contractor_repository = ContractorRepository(db_manager)

    def save(self, container: Container) -> Container:
        """
        Create or update a container.
        Performs business validations before saving.
        
        Args:
            container: Container object to save
            
        Returns:
            Saved Container with ID
            
        Raises:
            ValueError: If validation fails
        """
        self._validate_container(container)
        
        # Check for duplicate code
        existing = self.repository.get_by_code(container.code)
        if existing and existing.id != container.id:
            raise ValueError(f"Ya existe un contenedor con código '{container.code}'. Los códigos deben ser únicos para evitar confusiones en la báscula.")

        if container.id:
            return self.repository.update(container)
        else:
            return self.repository.add(container)

    def _validate_container(self, container: Container):
        """
        Validate business rules for container.
        
        Hard Constraints:
        - Code must be unique
        - Capacity must be between 5 and 40 m³
        - Contractor must be active
        """
        if not container.code or not container.code.strip():
            raise ValueError("El código del contenedor es obligatorio.")
        
        # Capacity validation: Industrial containers MUST be between 5 and 40 m³
        if container.capacity_m3 < 5 or container.capacity_m3 > 40:
            raise ValueError(
                f"La capacidad debe estar entre 5 y 40 m³. "
                f"Valor ingresado: {container.capacity_m3} m³. "
                f"Es imposible tener una tolva industrial fuera de este rango."
            )
        
        # Contractor integrity: Ensure contractor exists and is active
        if not container.contractor_id:
            raise ValueError("El contratista es obligatorio.")
        
        contractor = self.contractor_repository.get_by_id(container.contractor_id)
        if not contractor:
            raise ValueError(f"No existe un contratista con ID {container.contractor_id}.")
        
        if not contractor.is_active:
            raise ValueError(f"El contratista '{contractor.name}' no está activo. No se pueden asignar contenedores a contratistas inactivos.")
        
        # Status validation
        valid_statuses = ['AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED']
        if container.status not in valid_statuses:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}")

    def delete_container(self, container_id: int) -> bool:
        """
        Soft delete a container.
        """
        return self.repository.delete(container_id)

    def get_all_containers(self, active_only: bool = True) -> List[Container]:
        """
        Get all containers.
        """
        if active_only:
            return self.repository.get_all_active()
        else:
            return self.repository.get_all()

    def get_by_contractor(self, contractor_id: int, active_only: bool = True) -> List[Container]:
        """
        Get containers for a specific contractor.
        """
        return self.repository.get_by_contractor(contractor_id, active_only)

    def get_available_containers(self, plant_id: int = None) -> List[Container]:
        """
        Get containers with AVAILABLE status.
        If plant_id is provided, filter by location (future enhancement).
        """
        all_containers = self.repository.get_all_active()
        return [c for c in all_containers if c.status == 'AVAILABLE']

    def get_container_by_id(self, container_id: int) -> Optional[Container]:
        """
        Get a single container by ID.
        """
        return self.repository.get_by_id(container_id)

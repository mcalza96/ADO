from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from models.operations.load import Load

class DisposalExecutionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)

    def register_arrival(self, load_id: int, weight: float, observation: str = None) -> Load:
        """
        Orquesta el registro de llegada de una carga a portería/pesaje (TTO-03).
        Transiciona de Dispatched -> Arrived.
        
        Args:
            load_id: ID de la carga
            weight: Peso bruto registrado en báscula (kg)
            ph: pH registrado
            humidity: Humedad registrada (%)
            observation: Observaciones opcionales de calidad
            
        Returns:
            Load con estado actualizado a 'Arrived'
            
        Raises:
            ValueError: Si la carga no existe o no está en estado Dispatched
        """
        # 1. Obtener carga del repositorio
        load = self.load_repo.get_by_id(load_id)
        
        # 2. Validar existencia
        if not load:
            raise ValueError("Carga no encontrada")
        
        # 3. Delegar lógica de negocio al modelo de dominio
        load.register_arrival(weight, ph, humidity, observation)
        
        # 4. Persistir cambios
        if self.load_repo.update(load):
            return load
        else:
            raise Exception("Failed to update load in database")

    # --- Disposal Execution ---
    def get_pending_disposal_loads(self, site_id: int) -> List[Load]:
        """
        Loads that are 'Delivered' (Closed by Driver) at the site.
        These are ready for incorporation/disposal.
        """
        return self.load_repo.get_delivered_by_destination_type('DisposalSite', site_id)

    def execute_disposal(self, load_id: int, coordinates: str, treatment_facility_id: Optional[int] = None) -> Load:
        """
        Transition from PendingDisposal -> Disposed.
        
        Orchestrates the disposal process by delegating business logic to the Load entity.
        """
        # 1. Retrieve the load
        load = self.load_repo.get_by_id(load_id)
        
        # 2. Validate existence
        if not load:
            raise ValueError("Load not found")
        
        # 3. Delegate business logic to the domain model
        load.complete_disposal(coordinates, treatment_facility_id)
        
        # 4. Persist changes
        return self.load_repo.update(load)

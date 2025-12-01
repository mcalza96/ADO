from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from repositories.load_repository import LoadRepository
from services.operations.batch_service import BatchService
from models.operations.load import Load
from domain.exceptions import TransitionException

class ReceptionService:
    """
    Handles Reception and Disposal logic at the destination (Site or Plant).
    Responsibilities:
    - Tracking pending loads (InTransit)
    - Confirming arrival with weight adjustment (Sprint 2)
    - Executing Disposal (Legacy workflow)
    - Site Events
    """
    def __init__(self, db_manager: DatabaseManager, batch_service: Optional[BatchService] = None):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.batch_service = batch_service  # For inventory adjustment

    def confirm_arrival(
        self,
        load_id: int,
        arrival_time: datetime,
        final_weight: float,
        notes: Optional[str] = None
    ) -> Load:
        """
        Confirms arrival of a load for Sprint 2 workflow.
        Updates status to 'Delivered' and adjusts batch inventory if weight differs.
        
        Args:
            load_id: ID of the load to receive
            arrival_time: Datetime of arrival
            final_weight: Final weight in kg (actual measured)
            notes: Optional reception notes
            
        Returns:
            Updated Load object
            
        Raises:
            ValueError: If load not found
            TransitionException: If load is not in InTransit status
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Carga con ID {load_id} no encontrada")
        
        # State validation
        if load.status != 'InTransit':
            raise TransitionException(
                f"No se puede recepcionar. Estado actual: {load.status}. Esperado: 'InTransit'."
            )
        
        # Calculate weight difference
        estimated_weight = load.weight_net or 0
        weight_difference = final_weight - estimated_weight
        
        # Adjust batch inventory if there's a difference and batch_service is available
        if weight_difference != 0 and load.batch_id and self.batch_service:
            try:
                if weight_difference > 0:
                    # More weight than estimated: reserve additional tonnage
                    self.batch_service.reserve_tonnage(load.batch_id, weight_difference)
                else:
                    # Less weight than estimated: return excess tonnage
                    self.batch_service.return_tonnage(load.batch_id, abs(weight_difference))
            except ValueError as e:
                # Log warning but don't fail reception
                print(f"Warning: Could not adjust batch inventory: {str(e)}")
        
        # Update load
        load.status = 'Delivered'
        load.arrival_time = arrival_time
        load.weight_net = final_weight
        load.updated_at = datetime.now()
        
        # Update sync status
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        self.load_repo.update(load)
        return load

    def register_arrival(
        self,
        load_id: int,
        weight_gross: float,
        ph: float = None,
        humidity: float = None,
        observation: str = None
    ) -> Load:
        """
        Registra llegada con datos de calidad (TTO-02/TTO-03).
        Transiciona Load de 'InTransit' a 'Arrived'.
        
        Args:
            load_id: ID of the load arriving
            weight_gross: Gross weight measured at arrival (kg)
            ph: pH measurement (optional)
            humidity: Humidity percentage (optional)
            observation: Reception observations (optional)
            
        Returns:
            Updated Load object
            
        Raises:
            ValueError: If load not found
            TransitionException: If load is not in InTransit status
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Carga con ID {load_id} no encontrada")
        
        # Delegate to Load domain model for state transition
        load.register_arrival(weight_gross, ph, humidity, observation)
        
        # Persist changes
        self.load_repo.update(load)
        return load
    
    def get_in_transit_loads(self) -> List[Load]:
        """
        Returns all loads currently in transit, for reception view.
        """
        return self.load_repo.get_in_transit_loads()

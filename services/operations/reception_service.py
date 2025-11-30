from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from repositories.load_repository import LoadRepository
from services.operations.batch_service import BatchService
from models.operations.load import Load
from models.operations.site_event import SiteEvent
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
        self.event_repo = BaseRepository(db_manager, SiteEvent, "site_events")
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

    def get_in_transit_loads(self) -> List[Load]:
        """
        Returns all loads currently in transit, for reception view.
        """
        return self.load_repo.get_in_transit_loads()

    # --- Site Preparation ---
    def register_site_event(self, site_id: int, event_type: str, event_date: datetime, description: str = None) -> SiteEvent:
        event = SiteEvent(
            id=None,
            site_id=site_id,
            event_type=event_type,
            event_date=event_date,
            description=description,
            created_at=datetime.now()
        )
        return self.event_repo.add(event)

    def get_site_events(self, site_id: int) -> List[SiteEvent]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM site_events WHERE site_id = ? ORDER BY event_date DESC", (site_id,))
            rows = cursor.fetchall()
            return [SiteEvent(**dict(row)) for row in rows]

    # --- Disposal Execution (Legacy workflow) ---
    def register_arrival(self, load_id: int) -> Load:
        """
        Registers the arrival of the load at the destination.
        Status -> 'PendingDisposal'.
        This is for the disposal/agronomy workflow.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        # State Transition Validation
        if load.status != 'In Transit':
            raise TransitionException(f"Cannot register arrival. Current status: {load.status}. Expected: 'In Transit'.")
            
        load.status = 'PendingDisposal'
        load.arrival_time = datetime.now()
        load.updated_at = datetime.now()
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def get_pending_disposal_loads(self, site_id: int) -> List[Load]:
        """Loads that are PendingDisposal (Unloaded by Transport) at the site."""
        return self.load_repo.get_by_destination_and_status(site_id, 'PendingDisposal')

    def execute_disposal(self, load_id: int, coordinates: str, treatment_facility_id: Optional[int] = None) -> Load:
        """Transition from PendingDisposal -> Disposed"""
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'PendingDisposal':
            raise TransitionException(f"Load must be PendingDisposal to execute disposal. Current: {load.status}")
            
        load.status = 'Disposed'
        load.disposal_time = datetime.now()
        load.disposal_coordinates = coordinates
        if treatment_facility_id:
            load.treatment_facility_id = treatment_facility_id
            
        load.updated_at = datetime.now()
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
            
        return self.load_repo.update(load)


from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from repositories.site_event_repository import SiteEventRepository
from models.operations.load import Load
from models.operations.site_event import SiteEvent

class DisposalExecutionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.event_repo = SiteEventRepository(db_manager)

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
        return self.event_repo.get_by_site_id(site_id)

    # --- Load Reception (Gate) ---
    # DEPRECATED: Gate reception removed. Transport directly transitions to PendingDisposal.
    # def get_incoming_loads(self, site_id: int) -> List[Load]: ...
    # def register_arrival(self, load_id: int) -> Load: ...

    # --- Disposal Execution ---
    def get_pending_disposal_loads(self, site_id: int) -> List[Load]:
        """Loads that are PendingDisposal (Unloaded by Transport) at the site."""
        return self.load_repo.get_pending_disposal_by_site(site_id)

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

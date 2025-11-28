from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.operations.load import Load
from models.operations.site_event import SiteEvent

class DisposalExecutionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = BaseRepository(db_manager, Load, "loads")
        self.event_repo = BaseRepository(db_manager, SiteEvent, "site_events")

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

    # --- Load Reception (Gate) ---
    # DEPRECATED: Gate reception removed. Transport directly transitions to PendingDisposal.
    # def get_incoming_loads(self, site_id: int) -> List[Load]: ...
    # def register_arrival(self, load_id: int) -> Load: ...

    # --- Disposal Execution ---
    def get_pending_disposal_loads(self, site_id: int) -> List[Load]:
        """Loads that are PendingDisposal (Unloaded by Transport) at the site."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM loads WHERE destination_site_id = ? AND status = 'PendingDisposal'", (site_id,))
            rows = cursor.fetchall()
            return [Load(**dict(row)) for row in rows]

    def execute_disposal(self, load_id: int, coordinates: str, treatment_facility_id: Optional[int] = None) -> Load:
        """Transition from PendingDisposal -> Disposed"""
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'PendingDisposal':
            raise ValueError(f"Load must be PendingDisposal to execute disposal. Current: {load.status}")
            
        load.status = 'Disposed'
        load.disposal_time = datetime.now()
        load.disposal_coordinates = coordinates
        if treatment_facility_id:
            load.treatment_facility_id = treatment_facility_id
            
        return self.load_repo.update(load)

from typing import List
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.site_event_repository import SiteEventRepository
from models.operations.site_event import SiteEvent

class SitePreparationService:
    """
    Handles Site Preparation and Event Logging (DO-06 to DO-16).
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.event_repo = SiteEventRepository(db_manager)

    def register_site_event(self, site_id: int, event_type: str, event_date: datetime, description: str = None) -> SiteEvent:
        """
        Registers a new site event (e.g., Preparation, Closure).
        """
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
        """
        Retrieves history of events for a site.
        """
        return self.event_repo.get_by_site_id(site_id)

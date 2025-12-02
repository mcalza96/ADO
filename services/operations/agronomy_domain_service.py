from typing import List, Optional, Dict
from datetime import datetime, date
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from repositories.load_repository import LoadRepository
from models.operations.load import Load
from models.operations.site_event import SiteEvent
from models.agronomy.application import NitrogenApplication
from services.compliance.compliance_service import ComplianceService

class AgronomyDomainService:
    """
    Handles all agronomic operations:
    - Site Preparation & Events
    - Disposal Execution (Incorporation)
    - Nitrogen Application Tracking
    """
    def __init__(self, db_manager: DatabaseManager, compliance_service: ComplianceService):
        self.db_manager = db_manager
        self.compliance_service = compliance_service
        self.load_repo = LoadRepository(db_manager)
        self.event_repo = BaseRepository(db_manager, SiteEvent, "site_events")
        self.application_repo = BaseRepository(db_manager, NitrogenApplication, "nitrogen_applications")

    # --- Site Events ---
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
        return self.event_repo.get_by_attribute("site_id", site_id) or []

    # --- Nitrogen Tracking ---
    def register_nitrogen_application(self, site_id: int, load_id: int, batch_id: int, weight_net: float) -> None:
        """
        Registers a nitrogen application for a dispatched load.
        """
        try:
            # Calculate actual N applied
            agronomics = self.compliance_service.calculate_load_agronomics(batch_id, weight_net)
            nitrogen_kg = agronomics['total_n_kg']
            
            app = NitrogenApplication(
                id=None,
                site_id=site_id,
                load_id=load_id,
                nitrogen_applied_kg=nitrogen_kg,
                application_date=date.today()
            )
            self.application_repo.add(app)
        except Exception as e:
            print(f"Warning: Failed to register nitrogen application: {str(e)}")

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
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        load.complete_disposal(coordinates, treatment_facility_id)
        
        if self.load_repo.update(load):
            return load
        else:
            raise Exception("Failed to update load in database")

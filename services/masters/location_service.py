from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.facility_repository import FacilityRepository
from repositories.site_repository import SiteRepository
from models.masters.location import Facility, Site


class LocationService:
    def __init__(self, db_manager: DatabaseManager):
        self.facility_repo = FacilityRepository(db_manager)
        self.site_repo = SiteRepository(db_manager)
        self.db_manager = db_manager

    def get_facility_by_id(self, facility_id: int) -> Optional[Facility]:
        return self.facility_repo.get_by_id(facility_id)

    def update_facility_allowed_vehicle_types(self, facility_id: int, allowed_types: str) -> bool:
        return self.facility_repo.update_allowed_vehicle_types(facility_id, allowed_types)

    # --- Facilities ---
    def get_facilities_by_client(self, client_id: int) -> List[Facility]:
        return self.facility_repo.get_by_client(client_id)

    def create_facility(self, facility: Facility) -> Facility:
        return self.facility_repo.add(facility)
    
    def get_all_facilities(self) -> List[Facility]:
        return self.facility_repo.get_all_active()

    # --- Sites ---
    def get_all_sites(self) -> List[Site]:
        return self.site_repo.get_all(order_by="name")

    def create_site(self, site: Site) -> Site:
        return self.site_repo.add(site)
    
    def get_site_by_id(self, site_id: int) -> Optional[Site]:
        return self.site_repo.get_by_id(site_id)


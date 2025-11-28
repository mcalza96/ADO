from typing import List
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.location import Facility, Site

class LocationService:
    def get_facility_by_id(self, facility_id: int) -> Facility:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facilities WHERE id = ?", (facility_id,))
            row = cursor.fetchone()
            return Facility(**dict(row)) if row else None

    def update_facility_allowed_vehicle_types(self, facility_id: int, allowed_types: str) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE facilities SET allowed_vehicle_types = ? WHERE id = ?", (allowed_types, facility_id))
            conn.commit()
            return cursor.rowcount > 0
    def __init__(self, db_manager: DatabaseManager):
        self.facility_repo = BaseRepository(db_manager, Facility, "facilities")
        self.site_repo = BaseRepository(db_manager, Site, "sites")
        self.db_manager = db_manager

    # --- Facilities ---
    def get_facilities_by_client(self, client_id: int) -> List[Facility]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM facilities WHERE client_id = ? AND is_active = 1", (client_id,))
            rows = cursor.fetchall()
            return [Facility(**dict(row)) for row in rows]

    def create_facility(self, facility: Facility) -> Facility:
        return self.facility_repo.add(facility)

    # --- Sites ---
    def get_all_sites(self) -> List[Site]:
        return self.site_repo.get_all(order_by="name")

    def create_site(self, site: Site) -> Site:
        return self.site_repo.add(site)

from typing import List, Optional
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.treatment_plant import TreatmentPlant
from repositories.facility_repository import FacilityRepository

class TreatmentPlantService:
    def __init__(self, db_manager: DatabaseManager):
        self.repo = FacilityRepository(db_manager)

    def get_all(self) -> List[TreatmentPlant]:
        return self.repo.get_all()

    def get_all_plants(self) -> List[TreatmentPlant]:
        return self.repo.get_all()

    def get_by_id(self, facility_id: int) -> Optional[TreatmentPlant]:
        return self.repo.get_by_id(facility_id)

    def get_facilities_by_client(self, client_id: int) -> List[TreatmentPlant]:
        if not client_id: return []
        return self.repo.get_by_client_id(client_id)

    def get_plant_by_id(self, plant_id: int) -> Optional[TreatmentPlant]:
        """Return a TreatmentPlant by its ID or None if not found."""
        return self.repo.get_by_id(plant_id)

    def create_plant(self, name: str, address: str) -> TreatmentPlant:
        plant = TreatmentPlant(
            id=None,
            name=name,
            address=address,
            authorization_resolution=None
        )
        return self.repo.add(plant)

    def update_plant(self, plant: TreatmentPlant) -> bool:
        return self.repo.update(plant)

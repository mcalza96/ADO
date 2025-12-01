from typing import List, Optional
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.treatment_plant import TreatmentPlant
from repositories.treatment_plant_repository import TreatmentPlantRepository

class TreatmentPlantService:
    """
    Service layer for Treatment Plant (Facility) entity.
    Consolidates logic from the old FacilityService.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repo = TreatmentPlantRepository(db_manager)

    def get_all(self, active_only: bool = True) -> List[TreatmentPlant]:
        """Get all plants, optionally filtered by active status."""
        return self.repo.get_all(active_only=active_only, order_by="name")

    def get_by_id(self, plant_id: int) -> Optional[TreatmentPlant]:
        """Return a TreatmentPlant by its ID or None if not found."""
        return self.repo.get_by_id(plant_id)

    def get_by_client(self, client_id: int, active_only: bool = True) -> List[TreatmentPlant]:
        """Get all plants for a specific client."""
        if not client_id: return []
        plants = self.repo.get_by_client_id(client_id)
        if active_only:
            return [p for p in plants if p.is_active]
        return plants

    def save(self, plant: TreatmentPlant) -> TreatmentPlant:
        """
        Save a plant (create new or update existing).
        Includes business validation.
        """
        # Business validation
        if not plant.name or not plant.name.strip():
            raise ValueError("El nombre de la planta es obligatorio.")
        
        if not plant.client_id:
            raise ValueError("La planta debe estar asociada a un cliente.")

        if plant.id is None:
            return self.repo.add(plant)
        else:
            if self.repo.update(plant):
                return plant
            raise Exception(f"Error updating plant {plant.id}")

    def delete(self, plant_id: int) -> bool:
        """Soft delete a plant."""
        return self.repo.soft_delete(plant_id)


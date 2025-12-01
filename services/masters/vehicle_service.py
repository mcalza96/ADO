from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.vehicle_repository import VehicleRepository
from models.masters.vehicle import Vehicle

class VehicleService:
    def __init__(self, vehicle_repository: VehicleRepository):
        self.repository = vehicle_repository

    def save(self, vehicle: Vehicle) -> Vehicle:
        """
        Create or update a vehicle.
        Performs validations before saving.
        """
        self._validate_vehicle(vehicle)
        
        # Check for duplicate license plate
        existing = self.repository.get_by_license_plate(vehicle.license_plate)
        if existing and existing.id != vehicle.id:
            raise ValueError(f"Vehicle with license plate {vehicle.license_plate} already exists.")

        if vehicle.id:
            return self.repository.update(vehicle)
        else:
            return self.repository.add(vehicle)

    def _validate_vehicle(self, vehicle: Vehicle):
        """
        Validate business rules for vehicle.
        """
        if not vehicle.license_plate:
            raise ValueError("License plate is required.")
        
        if vehicle.capacity_wet_tons <= 0 or vehicle.capacity_wet_tons > 40:
            raise ValueError("Capacity must be between 0 and 40 tons.")
            
        if not vehicle.contractor_id:
             raise ValueError("Contractor is required.")

    def delete_vehicle(self, vehicle_id: int) -> bool:
        """
        Soft delete a vehicle.
        """
        return self.repository.delete(vehicle_id)

    def get_all_vehicles(self, active_only: bool = True) -> List[Vehicle]:
        """
        Get all vehicles.
        """
        return self.repository.get_all(active_only=active_only)

    def get_vehicles_by_contractor(self, contractor_id: int) -> List[Vehicle]:
        """
        Get all active vehicles for a specific contractor.
        """
        return self.repository.get_by_contractor(contractor_id)

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """
        Get a vehicle by ID.
        """
        return self.repository.get_by_id(vehicle_id)
        if active_only:
            return self.repository.get_all_active()
        else:
            return self.repository.get_all()

    def get_by_contractor(self, contractor_id: int) -> List[Vehicle]:
        """
        Get vehicles for a specific contractor.
        """
        return self.repository.get_by_contractor(contractor_id)

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.repository.get_by_id(vehicle_id)

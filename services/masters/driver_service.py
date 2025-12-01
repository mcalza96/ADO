from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.driver_repository import DriverRepository
from repositories.contractor_repository import ContractorRepository
from models.masters.driver import Driver

class DriverService:
    def __init__(self, driver_repository: DriverRepository, contractor_repository: ContractorRepository):
        self.repository = driver_repository
        self.contractor_repository = contractor_repository

    def save(self, driver: Driver) -> Driver:
        """
        Create or update a driver.
        Performs validations before saving.
        """
        self._validate_driver(driver)
        
        # Check for duplicate RUT
        if driver.rut:
            existing = self.repository.get_by_rut(driver.rut)
            if existing and existing.id != driver.id:
                raise ValueError(f"Driver with RUT {driver.rut} already exists.")

        if driver.id:
            return self.repository.update(driver)
        else:
            return self.repository.add(driver)

    def _validate_driver(self, driver: Driver):
        """
        Validate business rules for driver.
        """
        if not driver.name:
            raise ValueError("Name is required.")
        
        if not driver.contractor_id:
             raise ValueError("Contractor is required.")
             
        # Validate contractor exists and is active
        contractor = self.contractor_repository.get_by_id(driver.contractor_id)
        if not contractor or not contractor.is_active:
            raise ValueError(f"Contractor with ID {driver.contractor_id} is not valid or inactive.")

    def delete_driver(self, driver_id: int) -> bool:
        """
        Soft delete a driver.
        """
        return self.repository.delete(driver_id)

    def get_drivers_by_contractor(self, contractor_id: int) -> List[Driver]:
        """
        Get all active drivers for a specific contractor.
        """
        return self.repository.get_by_contractor(contractor_id)

    def get_driver_by_id(self, driver_id: int) -> Optional[Driver]:
        """
        Get a driver by ID.
        """
        return self.repository.get_by_id(driver_id)

    def get_all_drivers(self, active_only: bool = True) -> List[Driver]:
        """
        Get all drivers.
        """
        if active_only:
            return self.repository.get_all_active()
        else:
            return self.repository.get_all()

    def get_by_contractor(self, contractor_id: int) -> List[Driver]:
        """
        Get drivers for a specific contractor.
        """
        return self.repository.get_by_contractor(contractor_id)

    def get_driver_by_id(self, driver_id: int) -> Optional[Driver]:
        return self.repository.get_by_id(driver_id)

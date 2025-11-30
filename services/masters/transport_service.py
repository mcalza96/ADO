from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.contractor_repository import ContractorRepository
from repositories.vehicle_repository import VehicleRepository
from models.masters.transport import Contractor, Driver, Vehicle
from models.operations.load import Load
from database.repository import BaseRepository


class TransportService:
    def __init__(self, db_manager: DatabaseManager):
        self.contractor_repo = ContractorRepository(db_manager)
        self.vehicle_repo = VehicleRepository(db_manager)
        self.driver_repo = BaseRepository(db_manager, Driver, "drivers")
        from repositories.load_repository import LoadRepository
        self.load_repo = LoadRepository(db_manager)
        self.db_manager = db_manager  # Keep ref if needed for custom queries

    # --- Contractors ---
    def get_all_contractors(self) -> List[Contractor]:
        return self.contractor_repo.get_all_active()

    def create_contractor(self, contractor: Contractor) -> Contractor:
        return self.contractor_repo.add(contractor)
    
    def get_contractor_by_id(self, contractor_id: int) -> Optional[Contractor]:
        return self.contractor_repo.get_by_id(contractor_id)

    # --- Drivers ---
    def get_drivers_by_contractor(self, contractor_id: int) -> List[Driver]:
        # Custom query needed for filtering
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE contractor_id = ? AND is_active = 1", (contractor_id,))
            rows = cursor.fetchall()
            return [Driver(**dict(row)) for row in rows]

    def create_driver(self, driver: Driver) -> Driver:
        return self.driver_repo.add(driver)

    def get_driver_by_id(self, driver_id: int) -> Optional[Driver]:
        return self.driver_repo.get_by_id(driver_id)

    # --- Vehicles ---
    def get_vehicles_by_contractor(self, contractor_id: int) -> List[Vehicle]:
        return self.vehicle_repo.get_by_contractor(contractor_id)

    def get_all_active_vehicles(self) -> List[Vehicle]:
        return self.vehicle_repo.get_all_active()

    def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """
        Creates a new vehicle with validation.
        
        CRITICAL BUSINESS RULE: tare_weight must be strictly less than max_capacity.
        
        Args:
            vehicle: Vehicle entity to create
            
        Returns:
            Created vehicle with ID assigned
            
        Raises:
            ValueError: If tare_weight >= max_capacity
        """
        if vehicle.tare_weight >= vehicle.max_capacity:
            raise ValueError("La tara debe ser estrictamente menor que la capacidad máxima")
        
        return self.vehicle_repo.add(vehicle)
    
    def update_vehicle(self, vehicle: Vehicle) -> bool:
        """
        Updates an existing vehicle with validation.
        
        CRITICAL BUSINESS RULE: tare_weight must be strictly less than max_capacity.
        
        Args:
            vehicle: Vehicle entity to update
            
        Returns:
            True if update was successful
            
        Raises:
            ValueError: If tare_weight >= max_capacity
        """
        if vehicle.tare_weight >= vehicle.max_capacity:
            raise ValueError("La tara debe ser estrictamente menor que la capacidad máxima")
        
        return self.vehicle_repo.update(vehicle)

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.vehicle_repo.get_by_id(vehicle_id)

    def get_driver_loads(self, vehicle_plate: str) -> List[Load]:
        """
        Obtiene las cargas activas asignadas a un vehículo por su patente.
        
        Lógica:
        1. Buscar vehículo por patente usando VehicleRepository.get_by_license_plate()
        2. Si no existe, retornar lista vacía
        3. Usar LoadRepository.get_active_loads_by_vehicle() para obtener cargas
        
        Args:
            vehicle_plate: Patente del vehículo (ej: "AB-1234")
            
        Returns:
            Lista de cargas activas del vehículo
        """
        vehicle = self.vehicle_repo.get_by_license_plate(vehicle_plate)
        if not vehicle:
            return []
            
        return self.load_repo.get_active_loads_by_vehicle(vehicle.id)


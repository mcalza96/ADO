from typing import List, Optional
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.transport import Contractor, Driver, Vehicle

class TransportService:
    def __init__(self, db_manager: DatabaseManager):
        self.contractor_repo = BaseRepository(db_manager, Contractor, "contractors")
        self.driver_repo = BaseRepository(db_manager, Driver, "drivers")
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.db_manager = db_manager # Keep ref if needed for custom queries

    # --- Contractors ---
    def get_all_contractors(self) -> List[Contractor]:
        return self.contractor_repo.get_all(order_by="name")

    def create_contractor(self, contractor: Contractor) -> Contractor:
        return self.contractor_repo.add(contractor)

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
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicles WHERE contractor_id = ? AND is_active = 1", (contractor_id,))
            rows = cursor.fetchall()
            return [Vehicle(**dict(row)) for row in rows]

    def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        return self.vehicle_repo.add(vehicle)

    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        return self.vehicle_repo.get_by_id(vehicle_id)

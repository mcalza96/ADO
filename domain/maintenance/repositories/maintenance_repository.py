from typing import List, Optional
from database.repository import BaseRepository
from domain.maintenance.entities.maintenance_plan import MaintenancePlan, MaintenanceOrder
from database.db_manager import DatabaseManager

class MaintenancePlanRepository(BaseRepository[MaintenancePlan]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, MaintenancePlan, "maintenance_plans")
    
    def get_active_plans_by_asset(self, asset_id: int) -> List[MaintenancePlan]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE asset_id = ? AND is_active = 1",
                (asset_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

class MaintenanceOrderRepository(BaseRepository[MaintenanceOrder]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, MaintenanceOrder, "maintenance_orders")
    
    def get_pending_orders(self, asset_id: int) -> List[MaintenanceOrder]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE asset_id = ? AND status = 'PENDING'",
                (asset_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

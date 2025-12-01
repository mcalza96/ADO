from typing import List
from database.repository import BaseRepository
from models.operations.load import Load
from database.db_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def get_all_ordered_by_date(self) -> List[Load]:
        """
        Returns all loads ordered by scheduled_date DESC.
        """
        return self.get_all(order_by="scheduled_date DESC")

    def get_by_status(self, status: str) -> List[Load]:
        """
        Returns loads filtered by status, ordered by created_at DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC", (status,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_origin_facility(self, facility_id: int) -> List[Load]:
        """
        Returns loads filtered by origin_facility_id, ordered by scheduled_date DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE origin_facility_id = ? ORDER BY scheduled_date DESC", (facility_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_destination_and_status(self, destination_site_id: int, status: str) -> List[Load]:
        """
        Returns loads filtered by destination_site_id and status.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE destination_site_id = ? AND status = ?", (destination_site_id, status))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_pending_disposal_by_site(self, site_id: int) -> List[Load]:
        """
        Returns loads that are PendingDisposal at the given site.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE destination_site_id = ? AND status = 'PendingDisposal'", (site_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def create_load(self, load: Load) -> Load:
        """
        Creates a new load with initial status='InTransit' for dispatch workflow.
        """
        return self.add(load)

    def update_to_delivered(self, load_id: int, arrival_time, final_weight: float) -> bool:
        """
        Updates a load to 'Delivered' status with arrival time and final weight.
        Used in reception workflow.
        
        Args:
            load_id: ID of the load to update
            arrival_time: Datetime of arrival
            final_weight: Final weight in kg (may differ from estimated)
        
        Returns:
            True if update successful, False otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET status = 'Delivered', arrival_time = ?, weight_net = ? WHERE id = ?",
                (arrival_time, final_weight, load_id)
            )
            return cursor.rowcount > 0

    def get_in_transit_loads(self) -> List[Load]:
        """
        Returns all loads with status='InTransit' for reception view.
        Ordered by dispatch_time DESC (most recent first).
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE status = 'InTransit' ORDER BY dispatch_time DESC")
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_active_loads_by_vehicle(self, vehicle_id: int) -> List[Load]:
        """
        Returns active loads assigned to a specific vehicle.
        Active loads are those with status: 'Requested', 'Scheduled', or 'Dispatched'.
        Ordered by scheduled_date DESC (most recent first).
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            List of active loads assigned to the vehicle
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} "
                f"WHERE vehicle_id = ? AND status IN ('Requested', 'Scheduled', 'Dispatched') "
                f"ORDER BY scheduled_date DESC",
                (vehicle_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_delivered_by_destination_type(self, destination_type: str, destination_id: int) -> List[Load]:
        """
        Returns loads that are 'Delivered' and waiting for the next stage (Disposal or Treatment).
        
        Args:
            destination_type: 'DisposalSite' or 'TreatmentPlant'
            destination_id: ID of the destination site or plant
            
        Returns:
            List of Delivered loads at the specified destination
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            if destination_type == 'DisposalSite':
                query = f"SELECT * FROM {self.table_name} WHERE status = 'Delivered' AND destination_site_id = ? ORDER BY arrival_time DESC"
                params = (destination_id,)
            elif destination_type == 'TreatmentPlant':
                query = f"SELECT * FROM {self.table_name} WHERE status = 'Delivered' AND destination_treatment_plant_id = ? ORDER BY arrival_time DESC"
                params = (destination_id,)
            else:
                return []
                
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_assignable_loads(self, vehicle_id: int) -> List[dict]:
        """
        Returns scheduled loads assigned to a specific vehicle with origin and destination names.
        This is for the driver to see available trips to accept.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            List of dicts containing load data with origin_facility_name and destination_site_name
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    l.*,
                    f.name AS origin_facility_name,
                    s.name AS destination_site_name
                FROM loads l
                LEFT JOIN facilities f ON l.origin_facility_id = f.id
                LEFT JOIN sites s ON l.destination_site_id = s.id
                WHERE l.vehicle_id = ? AND l.status = 'Scheduled'
                ORDER BY l.scheduled_date DESC
            """, (vehicle_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_active_load(self, vehicle_id: int) -> dict:
        """
        Returns the current active load for a specific vehicle.
        Active loads are those with status: 'Accepted', 'InTransit', or 'Arrived'.
        There should only be ONE active load per vehicle at any time.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            Dict containing load data with origin_facility_name and destination_site_name, or None
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    l.*,
                    f.name AS origin_facility_name,
                    s.name AS destination_site_name
                FROM loads l
                LEFT JOIN facilities f ON l.origin_facility_id = f.id
                LEFT JOIN sites s ON l.destination_site_id = s.id
                WHERE l.vehicle_id = ? AND l.status IN ('Accepted', 'InTransit', 'Arrived')
                ORDER BY l.dispatch_time DESC
                LIMIT 1
            """, (vehicle_id,))
            row = cursor.fetchone()
            return dict(row) if row else None


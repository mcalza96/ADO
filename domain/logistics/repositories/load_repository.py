from typing import List, Optional, Dict
from datetime import datetime
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from infrastructure.persistence.database_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def _map_row_to_model(self, row: dict) -> Load:
        """
        Override to handle datetime conversion from SQLite strings.
        Also ensures weight_net alias is populated from net_weight.
        """
        data = dict(row)
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at', 'dispatch_time', 'arrival_time', 'completion_time']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                try:
                    # Handle format "YYYY-MM-DD HH:MM:SS.ssssss" or "YYYY-MM-DD HH:MM:SS"
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    # Fallback or log error
                    pass
        
        # Ensure weight_net alias is populated from net_weight
        if 'net_weight' in data and data['net_weight'] is not None:
            data['weight_net'] = data['net_weight']
                    
        return super()._map_row_to_model(data)

    def get_next_manifest_sequence(self) -> int:
        """
        Returns the next sequence number using the sequences table.
        Thread-safe implementation using atomic update.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Atomic update
            cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'manifest_code'")
            
            # If no row updated (should not happen if migration ran), insert it
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO sequences (name, current_value) VALUES ('manifest_code', 1)")
                return 1
                
            # Retrieve the new value
            cursor.execute("SELECT current_value FROM sequences WHERE name = 'manifest_code'")
            row = cursor.fetchone()
            return row['current_value'] if row else 1

    def get_all(self, limit: int = 50, offset: int = 0) -> List[Load]:
        """
        Get all loads with pagination.
        Overrides BaseRepository.get_all to enforce limits.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_active_loads(self) -> List[Load]:
        """
        Returns all loads that are NOT 'COMPLETED' or 'CANCELLED'.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status NOT IN ('COMPLETED', 'CANCELLED') ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_active_load(self, vehicle_id: int) -> Optional[Load]:
        """
        Returns the active load for a specific vehicle, if any.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE vehicle_id = ? AND status NOT IN ('COMPLETED', 'CANCELLED') LIMIT 1",
                (vehicle_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(dict(row)) if row else None

    def get_assignable_loads(self, vehicle_id: int) -> List[Load]:
        """
        Returns loads that can be assigned to a vehicle (ASSIGNED status).
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at ASC",
                (LoadStatus.ASSIGNED.value,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_assigned_loads_by_vehicle(self, vehicle_id: int) -> List[Load]:
        """
        Returns loads with status ASSIGNED or ACCEPTED for a specific vehicle.
        
        Used by the driver dispatch view to show trips assigned to their vehicle.
        
        Args:
            vehicle_id: ID of the vehicle to filter by
            
        Returns:
            List of loads assigned to the vehicle
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE vehicle_id = ? 
                    AND status IN (?, ?) 
                    ORDER BY scheduled_date ASC, created_at ASC""",
                (vehicle_id, LoadStatus.ASSIGNED.value, LoadStatus.ACCEPTED.value)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_in_transit_loads_by_destination_site(self, site_id: int) -> List[Load]:
        """
        Returns loads in transit (EN_ROUTE_DESTINATION) heading to a specific disposal site.
        
        Used by disposal reception to show incoming trucks.
        
        Args:
            site_id: ID of the destination site
            
        Returns:
            List of loads in transit to the site
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE destination_site_id = ? 
                    AND status = ? 
                    ORDER BY dispatch_time ASC""",
                (site_id, LoadStatus.EN_ROUTE_DESTINATION.value)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_in_transit_loads_by_treatment_plant(self, plant_id: int) -> List[Load]:
        """
        Returns loads in transit (EN_ROUTE_DESTINATION) heading to a specific treatment plant.
        
        Used by treatment reception to show incoming trucks.
        
        Args:
            plant_id: ID of the destination treatment plant
            
        Returns:
            List of loads in transit to the plant
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE destination_treatment_plant_id = ? 
                    AND status = ? 
                    ORDER BY dispatch_time ASC""",
                (plant_id, LoadStatus.EN_ROUTE_DESTINATION.value)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_delivered_by_destination_type(self, destination_type: str, destination_id: int) -> List[Load]:
        """
        Returns loads that have been delivered (AT_DESTINATION or COMPLETED status) filtered by destination type and ID.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {self.table_name} WHERE status IN (?, ?)"
            params = [LoadStatus.AT_DESTINATION.value, LoadStatus.COMPLETED.value]
            
            if destination_type == 'TreatmentPlant':
                query += " AND destination_treatment_plant_id = ?"
                params.append(destination_id)
            elif destination_type == 'Site':
                query += " AND destination_site_id = ?"
                params.append(destination_id)
                
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_status(self, status: str, limit: int = 50) -> List[Load]:
        """
        Returns loads filtered by status, ordered by created_at DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_loads_with_details(self, status: Optional[str] = None, limit: int = 100) -> List[dict]:
        """
        Optimized query to fetch loads with related entity names (N+1 solution).
        Returns a list of dictionaries ready for UI display.
        """
        query = """
            SELECT 
                l.id, 
                l.status,
                l.scheduled_date,
                l.created_at,
                l.net_weight as weight_net,
                l.origin_facility_id,
                l.origin_treatment_plant_id,
                l.vehicle_type_requested,
                v.license_plate as vehicle_plate,
                d.name as driver_name,
                COALESCE(f.name, otp.name) as origin_facility_name,
                COALESCE(f.allowed_vehicle_types, l.vehicle_type_requested) as origin_allowed_vehicle_types,
                s.name as destination_site_name,
                tp.name as destination_plant_name
            FROM loads l
            LEFT JOIN vehicles v ON l.vehicle_id = v.id
            LEFT JOIN drivers d ON l.driver_id = d.id
            LEFT JOIN facilities f ON l.origin_facility_id = f.id
            LEFT JOIN treatment_plants otp ON l.origin_treatment_plant_id = otp.id
            LEFT JOIN sites s ON l.destination_site_id = s.id
            LEFT JOIN facilities tp ON l.destination_treatment_plant_id = tp.id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND l.status = ?"
            params.append(status)
            
        query += " ORDER BY l.created_at DESC LIMIT ?"
        params.append(limit)
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_loads_by_trip_id(self, trip_id: str) -> List[Load]:
        """
        Returns all loads that share the same trip_id.
        
        Used for trip linking operations where multiple loads are grouped together.
        
        Args:
            trip_id: UUID of the trip
            
        Returns:
            List of loads in the trip
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE trip_id = ? ORDER BY created_at ASC",
                (trip_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_pending_loads_by_origin_and_date(
        self,
        origin_facility_id: int,
        date_start: datetime,
        date_end: datetime
    ) -> List[Load]:
        """
        Returns pending loads (REQUESTED status) from a specific origin within a date range.
        
        Used to find candidate loads for trip linking.
        
        Args:
            origin_facility_id: ID of the origin facility
            date_start: Start of date range
            date_end: End of date range
            
        Returns:
            List of pending loads matching criteria
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE origin_facility_id = ? 
                    AND status = 'REQUESTED'
                    AND trip_id IS NULL
                    AND created_at BETWEEN ? AND ?
                    ORDER BY created_at ASC""",
                (origin_facility_id, date_start.isoformat(), date_end.isoformat())
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def update_trip_id_bulk(self, load_ids: List[int], trip_id: str, segment_types: Dict[int, str]) -> None:
        """
        Updates trip_id and segment_type for multiple loads in a single transaction.
        
        Used when linking loads into a trip.
        
        Args:
            load_ids: List of load IDs to update
            trip_id: UUID to assign to all loads
            segment_types: Map of load_id -> segment_type ('PICKUP_SEGMENT' or 'MAIN_HAUL')
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            for load_id in load_ids:
                segment_type = segment_types.get(load_id, 'DIRECT')
                cursor.execute(
                    f"""UPDATE {self.table_name} 
                        SET trip_id = ?, segment_type = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?""",
                    (trip_id, segment_type, load_id)
                )
            conn.commit()

    def update_financial_status_bulk(self, load_ids: List[int], status: str) -> None:
        """
        Updates financial_status for multiple loads.
        
        Args:
            load_ids: List of load IDs to update
            status: New status ('OPEN', 'CLOSED', 'BILLED')
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # SQLite doesn't support array parameters directly, so we loop or build dynamic query
            # For safety and simplicity with small batches, we'll loop or use executemany
            # executemany is better
            
            params = [(status, load_id) for load_id in load_ids]
            cursor.executemany(
                f"UPDATE {self.table_name} SET financial_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                params
            )
            conn.commit()
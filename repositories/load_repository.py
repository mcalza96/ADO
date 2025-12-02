from typing import List, Optional
from datetime import datetime
from database.repository import BaseRepository
from models.operations.load import Load
from database.db_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def _map_row_to_model(self, row: dict) -> Load:
        """
        Override to handle datetime conversion from SQLite strings.
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
        Returns loads that can be assigned to a vehicle (e.g., 'Scheduled').
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Assuming assignable loads are those with status 'Scheduled'
            # The vehicle_id parameter might be used for filtering if loads are pre-assigned to a vehicle
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status = 'Scheduled' ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_delivered_by_destination_type(self, destination_type: str, destination_id: int) -> List[Load]:
        """
        Returns loads that have been delivered (e.g., 'ARRIVED' or 'DISPATCHED') filtered by destination type and ID.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {self.table_name} WHERE status IN ('ARRIVED', 'DISPATCHED')"
            params = []
            
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
                l.manifest_code, 
                l.status,
                l.scheduled_date,
                l.created_at,
                c.name as contractor_name,
                v.license_plate as vehicle_plate,
                d.name as driver_name,
                f.name as origin_facility_name,
                s.name as destination_site_name,
                tp.name as destination_plant_name
            FROM loads l
            LEFT JOIN contractors c ON l.contractor_id = c.id
            LEFT JOIN vehicles v ON l.vehicle_id = v.id
            LEFT JOIN drivers d ON l.driver_id = d.id
            LEFT JOIN facilities f ON l.origin_facility_id = f.id
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
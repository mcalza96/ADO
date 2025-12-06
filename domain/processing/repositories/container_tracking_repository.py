from typing import List, Optional, Dict, Any
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager
from domain.logistics.entities.container_filling_record import ContainerFillingRecord, ContainerFillingStatus
from domain.logistics.entities.container import Container

class ContainerTrackingRepository:
    """
    Repository for managing container filling records and tracking.
    Encapsulates SQL operations for container tracking.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _row_to_record(self, row: Dict[str, Any]) -> ContainerFillingRecord:
        """Convert database row to ContainerFillingRecord, parsing datetime strings."""
        # Parse datetime fields
        datetime_fields = ['fill_end_time', 'ph_0h_recorded_at', 'ph_2h_recorded_at', 
                          'ph_24h_recorded_at', 'dispatched_at', 'created_at', 'updated_at']
        
        for field in datetime_fields:
            if field in row and row[field] and isinstance(row[field], str):
                try:
                    row[field] = datetime.fromisoformat(row[field])
                except (ValueError, TypeError):
                    row[field] = None
        
        return ContainerFillingRecord(**row)

    def create_filling_record(self, record: Dict[str, Any]) -> int:
        """Creates a new filling record and updates container status."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Insert the filling record
            cursor.execute("""
                INSERT INTO container_filling_records (
                    container_id, treatment_plant_id, fill_end_time,
                    humidity, ph_0h, ph_0h_recorded_at,
                    status, notes, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['container_id'], record['treatment_plant_id'], record['fill_end_time'],
                record['humidity'], record['ph_0h'], record['ph_0h_recorded_at'],
                record['status'], record['notes'], record['created_by'], 
                record['created_at'], record['updated_at']
            ))
            
            record_id = cursor.lastrowid
            
            # Update container status to IN_USE_TREATMENT
            cursor.execute("""
                UPDATE containers 
                SET status = 'IN_USE_TREATMENT', updated_at = ?
                WHERE id = ?
            """, (record['updated_at'], record['container_id']))
            
            conn.commit()
            return record_id

    def update_ph_measurement(self, record_id: int, field: str, value: float, recorded_at: datetime, status: Optional[str] = None) -> bool:
        """Updates a pH measurement (2h or 24h) and optionally status."""
        now = datetime.now().isoformat()
        recorded_at_iso = recorded_at.isoformat()
        
        # Determine which timestamp field to update
        timestamp_field = f"{field}_recorded_at"
        
        query = f"""
            UPDATE container_filling_records
            SET {field} = ?, {timestamp_field} = ?, updated_at = ?
        """
        params = [value, recorded_at_iso, now]
        
        if status:
            query += ", status = ?"
            params.append(status)
            
        query += " WHERE id = ?"
        params.append(record_id)
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def mark_as_dispatched(self, record_id: int, load_id: int, container_position: int) -> bool:
        """Marks a record as dispatched and updates container status."""
        now = datetime.now().isoformat()
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # 1. Get container_id from record
            cursor.execute("SELECT container_id FROM container_filling_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return False
            container_id = row['container_id']
            
            # 2. Update record status
            cursor.execute("""
                UPDATE container_filling_records
                SET status = ?, dispatched_load_id = ?, 
                    container_position = ?, dispatched_at = ?, updated_at = ?
                WHERE id = ?
            """, (
                ContainerFillingStatus.DISPATCHED.value,
                load_id, container_position, now, now, record_id
            ))
            
            # 3. Update container status back to AVAILABLE
            cursor.execute("""
                UPDATE containers 
                SET status = 'AVAILABLE', updated_at = ?
                WHERE id = ?
            """, (now, container_id))
            
            conn.commit()
            return True

    def get_active_records_by_plant(self, plant_id: int, status_filter: Optional[str] = None) -> List[ContainerFillingRecord]:
        """Get all active (non-dispatched) records for a plant."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    r.*, 
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records r
                JOIN containers c ON r.container_id = c.id
                LEFT JOIN treatment_plants tp ON r.treatment_plant_id = tp.id
                WHERE r.treatment_plant_id = ? 
                AND r.is_active = 1
            """
            params = [plant_id]
            
            if status_filter:
                query += " AND r.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY r.created_at DESC"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            return [self._row_to_record(dict(row)) for row in rows]

    def get_dispatchable_records(self, plant_id: int) -> List[ContainerFillingRecord]:
        """Get records ready for dispatch (READY_FOR_DISPATCH or FILLING/PENDING_PH but not DISPATCHED)."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.*, 
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records r
                JOIN containers c ON r.container_id = c.id
                LEFT JOIN treatment_plants tp ON r.treatment_plant_id = tp.id
                WHERE r.treatment_plant_id = ? 
                AND r.is_active = 1
                AND r.status != ?
                ORDER BY r.fill_end_time ASC
            """, (plant_id, ContainerFillingStatus.DISPATCHED.value))
            
            rows = cursor.fetchall()
            return [self._row_to_record(dict(row)) for row in rows]

    def get_by_id(self, record_id: int) -> Optional[ContainerFillingRecord]:
        """Get a record by ID."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.*, 
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records r
                JOIN containers c ON r.container_id = c.id
                LEFT JOIN treatment_plants tp ON r.treatment_plant_id = tp.id
                WHERE r.id = ? AND r.is_active = 1
            """, (record_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(dict(row))

    def is_container_in_use(self, container_id: int) -> bool:
        """Check if a container has an active record."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM container_filling_records 
                WHERE container_id = ? 
                AND status != ? 
                AND is_active = 1
            """, (container_id, ContainerFillingStatus.DISPATCHED.value))
            return cursor.fetchone() is not None

    def get_available_containers(self) -> List[Container]:
        """Get containers that are available for filling."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, co.name as contractor_name
                FROM containers c
                LEFT JOIN contractors co ON c.contractor_id = co.id
                WHERE c.is_active = 1 
                AND c.status = 'AVAILABLE'
                ORDER BY c.code
            """)
            
            containers = []
            for row in cursor.fetchall():
                data = dict(row)
                containers.append(Container(
                    id=data['id'],
                    contractor_id=data['contractor_id'],
                    code=data['code'],
                    capacity_m3=data['capacity_m3'],
                    status=data['status'],
                    is_active=data['is_active'],
                    contractor_name=data.get('contractor_name')
                ))
            return containers

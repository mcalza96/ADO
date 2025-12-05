"""
Container Tracking Service for Treatment Plant Operations.

Manages container filling records with pH/humidity measurements at 0, 2, and 24 hours.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from domain.logistics.entities.container_filling_record import (
    ContainerFillingRecord, 
    ContainerFillingStatus
)
from domain.logistics.entities.container import Container


class ContainerTrackingService:
    """
    Manages container tracking at treatment plants.
    
    Responsibilities:
    - Create filling records when container starts being filled
    - Track pH measurements at 0, 2, and 24 hours with time validation
    - Manage container status (AVAILABLE <-> IN_USE_TREATMENT)
    - Provide containers ready for dispatch
    - Mark containers as dispatched
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.container_repo = BaseRepository(db_manager, Container, "containers")
    
    # --- Container Filling Record Operations ---
    
    def create_filling_record(
        self,
        container_id: int,
        treatment_plant_id: int,
        fill_end_time: datetime,
        humidity: float,
        ph_0h: float,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ContainerFillingRecord:
        """
        Creates a new container filling record.
        
        Args:
            container_id: The container being filled
            treatment_plant_id: The treatment plant where filling occurred
            fill_end_time: When the container finished filling
            humidity: Initial humidity measurement (0-100%)
            ph_0h: Initial pH measurement (0-14)
            notes: Optional notes
            created_by: Username of the operator
            
        Returns:
            Created ContainerFillingRecord
            
        Raises:
            ValueError: If container is already in use or measurements are out of range
        """
        # Validate measurements
        if not 0 <= humidity <= 100:
            raise ValueError(f"Humedad debe estar entre 0 y 100%. Valor: {humidity}")
        if not 0 <= ph_0h <= 14:
            raise ValueError(f"pH debe estar entre 0 y 14. Valor: {ph_0h}")
        
        # Check container is not already in use
        if self._is_container_in_use(container_id):
            raise ValueError(f"El contenedor ya está en uso en otro registro activo")
        
        # Check container exists and is available
        container = self.container_repo.get_by_id(container_id)
        if not container:
            raise ValueError(f"Contenedor no encontrado: {container_id}")
        
        now = datetime.now()
        
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
                container_id, treatment_plant_id, fill_end_time.isoformat(),
                humidity, ph_0h, now.isoformat(),
                ContainerFillingStatus.PENDING_PH.value,
                notes, created_by, now.isoformat(), now.isoformat()
            ))
            
            record_id = cursor.lastrowid
            
            # Update container status to IN_USE_TREATMENT
            cursor.execute("""
                UPDATE containers 
                SET status = 'IN_USE_TREATMENT', updated_at = ?
                WHERE id = ?
            """, (now.isoformat(), container_id))
            
            conn.commit()
        
        return self.get_filling_record_by_id(record_id)
    
    def update_ph_2h(
        self,
        record_id: int,
        ph_value: float
    ) -> ContainerFillingRecord:
        """
        Record the 2-hour pH measurement.
        
        Args:
            record_id: The filling record ID
            ph_value: pH measurement (0-14)
            
        Returns:
            Updated ContainerFillingRecord
            
        Raises:
            ValueError: If timing constraint not met or pH out of range
        """
        if not 0 <= ph_value <= 14:
            raise ValueError(f"pH debe estar entre 0 y 14. Valor: {ph_value}")
        
        record = self.get_filling_record_by_id(record_id)
        if not record:
            raise ValueError(f"Registro no encontrado: {record_id}")
        
        if record.ph_2h is not None:
            raise ValueError("pH a 2 horas ya fue registrado")
        
        if not record.can_record_ph_2h:
            remaining = record.time_until_ph_2h
            if remaining:
                raise ValueError(
                    f"Debe esperar {remaining:.1f} horas más para registrar pH a 2 horas"
                )
            raise ValueError("No se puede registrar pH a 2 horas en este momento")
        
        now = datetime.now()
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE container_filling_records 
                SET ph_2h = ?, ph_2h_recorded_at = ?, updated_at = ?
                WHERE id = ?
            """, (ph_value, now.isoformat(), now.isoformat(), record_id))
            conn.commit()
        
        return self.get_filling_record_by_id(record_id)
    
    def update_ph_24h(
        self,
        record_id: int,
        ph_value: float
    ) -> ContainerFillingRecord:
        """
        Record the 24-hour pH measurement and mark as ready for dispatch.
        
        Args:
            record_id: The filling record ID
            ph_value: pH measurement (0-14)
            
        Returns:
            Updated ContainerFillingRecord
            
        Raises:
            ValueError: If timing constraint not met or pH out of range
        """
        if not 0 <= ph_value <= 14:
            raise ValueError(f"pH debe estar entre 0 y 14. Valor: {ph_value}")
        
        record = self.get_filling_record_by_id(record_id)
        if not record:
            raise ValueError(f"Registro no encontrado: {record_id}")
        
        if record.ph_24h is not None:
            raise ValueError("pH a 24 horas ya fue registrado")
        
        if not record.can_record_ph_24h:
            remaining = record.time_until_ph_24h
            if remaining:
                raise ValueError(
                    f"Debe esperar {remaining:.1f} horas más para registrar pH a 24 horas"
                )
            raise ValueError("No se puede registrar pH a 24 horas en este momento")
        
        now = datetime.now()
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE container_filling_records 
                SET ph_24h = ?, ph_24h_recorded_at = ?, 
                    status = ?, updated_at = ?
                WHERE id = ?
            """, (
                ph_value, now.isoformat(),
                ContainerFillingStatus.READY_FOR_DISPATCH.value,
                now.isoformat(), record_id
            ))
            conn.commit()
        
        return self.get_filling_record_by_id(record_id)
    
    def mark_as_dispatched(
        self,
        record_id: int,
        load_id: int,
        container_position: int
    ) -> ContainerFillingRecord:
        """
        Mark a container filling record as dispatched.
        
        Args:
            record_id: The filling record ID
            load_id: The load that is transporting this container
            container_position: Position on truck (1 or 2)
            
        Returns:
            Updated ContainerFillingRecord
        """
        if container_position not in (1, 2):
            raise ValueError("Posición del contenedor debe ser 1 o 2")
        
        record = self.get_filling_record_by_id(record_id)
        if not record:
            raise ValueError(f"Registro no encontrado: {record_id}")
        
        if record.status == ContainerFillingStatus.DISPATCHED.value:
            raise ValueError("Este contenedor ya fue despachado")
        
        now = datetime.now()
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Update filling record
            cursor.execute("""
                UPDATE container_filling_records 
                SET status = ?, dispatched_load_id = ?, 
                    dispatched_at = ?, container_position = ?, updated_at = ?
                WHERE id = ?
            """, (
                ContainerFillingStatus.DISPATCHED.value,
                load_id, now.isoformat(), container_position,
                now.isoformat(), record_id
            ))
            
            # Update container status back to AVAILABLE
            cursor.execute("""
                UPDATE containers 
                SET status = 'AVAILABLE', updated_at = ?
                WHERE id = ?
            """, (now.isoformat(), record.container_id))
            
            conn.commit()
        
        return self.get_filling_record_by_id(record_id)
    
    # --- Query Operations ---
    
    def get_filling_record_by_id(self, record_id: int) -> Optional[ContainerFillingRecord]:
        """Get a single filling record by ID with joined data."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    cfr.*,
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records cfr
                LEFT JOIN containers c ON cfr.container_id = c.id
                LEFT JOIN treatment_plants tp ON cfr.treatment_plant_id = tp.id
                WHERE cfr.id = ? AND cfr.is_active = 1
            """, (record_id,))
            
            row = cursor.fetchone()
            if row:
                return self._map_row_to_record(dict(row))
            return None
    
    def get_active_records_by_plant(
        self,
        treatment_plant_id: int,
        status_filter: Optional[str] = None
    ) -> List[ContainerFillingRecord]:
        """
        Get all active filling records for a treatment plant.
        
        Args:
            treatment_plant_id: The treatment plant ID
            status_filter: Optional status to filter by
            
        Returns:
            List of ContainerFillingRecord
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    cfr.*,
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records cfr
                LEFT JOIN containers c ON cfr.container_id = c.id
                LEFT JOIN treatment_plants tp ON cfr.treatment_plant_id = tp.id
                WHERE cfr.treatment_plant_id = ? AND cfr.is_active = 1
            """
            params = [treatment_plant_id]
            
            if status_filter:
                query += " AND cfr.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY cfr.created_at DESC"
            
            cursor.execute(query, params)
            
            return [self._map_row_to_record(dict(row)) for row in cursor.fetchall()]
    
    def get_records_ready_for_dispatch(
        self,
        treatment_plant_id: int
    ) -> List[ContainerFillingRecord]:
        """
        Get containers ready for dispatch from a treatment plant.
        These are containers with status READY_FOR_DISPATCH or FILLING
        (since container can leave while sample is kept for later pH measurements).
        """
        return self.get_active_records_by_plant(
            treatment_plant_id,
            status_filter=None  # Get all non-dispatched
        )
    
    def get_dispatchable_records(
        self,
        treatment_plant_id: int
    ) -> List[ContainerFillingRecord]:
        """
        Get containers that can be dispatched from a treatment plant.
        Returns records that are FILLING or READY_FOR_DISPATCH (not yet dispatched).
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    cfr.*,
                    c.code as container_code,
                    tp.name as treatment_plant_name
                FROM container_filling_records cfr
                LEFT JOIN containers c ON cfr.container_id = c.id
                LEFT JOIN treatment_plants tp ON cfr.treatment_plant_id = tp.id
                WHERE cfr.treatment_plant_id = ? 
                AND cfr.is_active = 1
                AND cfr.status != ?
                ORDER BY cfr.fill_end_time ASC
            """, (treatment_plant_id, ContainerFillingStatus.DISPATCHED.value))
            
            return [self._map_row_to_record(dict(row)) for row in cursor.fetchall()]
    
    def get_available_containers(
        self,
        treatment_plant_id: Optional[int] = None
    ) -> List[Container]:
        """
        Get containers that are available for filling.
        Excludes containers that are already in use (IN_USE_TREATMENT status).
        """
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
    
    def get_pending_ph_records(
        self,
        treatment_plant_id: int
    ) -> Dict[str, List[ContainerFillingRecord]]:
        """
        Get records with pending pH measurements, categorized by which pH is pending.
        
        Returns:
            Dict with keys 'pending_ph_2h' and 'pending_ph_24h'
        """
        records = self.get_active_records_by_plant(treatment_plant_id)
        
        pending_2h = []
        pending_24h = []
        
        for record in records:
            if record.status == ContainerFillingStatus.DISPATCHED.value:
                continue
            
            # Support both new (PENDING_PH) and legacy (FILLING) status
            if record.ph_2h is None and record.can_record_ph_2h:
                pending_2h.append(record)
            elif record.ph_24h is None and record.can_record_ph_24h:
                pending_24h.append(record)
        
        return {
            'pending_ph_2h': pending_2h,
            'pending_ph_24h': pending_24h
        }
    
    # --- Helper Methods ---
    
    def _is_container_in_use(self, container_id: int) -> bool:
        """Check if container has an active non-dispatched filling record."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM container_filling_records 
                WHERE container_id = ? 
                AND status != ? 
                AND is_active = 1
            """, (container_id, ContainerFillingStatus.DISPATCHED.value))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def _map_row_to_record(self, row: dict) -> ContainerFillingRecord:
        """Map a database row to ContainerFillingRecord."""
        return ContainerFillingRecord(
            id=row['id'],
            container_id=row['container_id'],
            treatment_plant_id=row['treatment_plant_id'],
            fill_end_time=self._parse_datetime(row['fill_end_time']),
            humidity=row['humidity'],
            ph_0h=row['ph_0h'],
            ph_0h_recorded_at=self._parse_datetime(row.get('ph_0h_recorded_at')),
            ph_2h=row.get('ph_2h'),
            ph_2h_recorded_at=self._parse_datetime(row.get('ph_2h_recorded_at')),
            ph_24h=row.get('ph_24h'),
            ph_24h_recorded_at=self._parse_datetime(row.get('ph_24h_recorded_at')),
            status=row['status'],
            dispatched_load_id=row.get('dispatched_load_id'),
            dispatched_at=self._parse_datetime(row.get('dispatched_at')),
            container_position=row.get('container_position'),
            notes=row.get('notes'),
            created_by=row.get('created_by'),
            is_active=row.get('is_active', True),
            created_at=self._parse_datetime(row.get('created_at')),
            updated_at=self._parse_datetime(row.get('updated_at')),
            container_code=row.get('container_code'),
            treatment_plant_name=row.get('treatment_plant_name')
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from string or return as-is if already datetime."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None


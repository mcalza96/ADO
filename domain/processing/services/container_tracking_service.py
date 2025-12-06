"""
Container Tracking Service for Treatment Plant Operations.

Manages container filling records with pH/humidity measurements at 0, 2, and 24 hours.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager
from domain.logistics.entities.container_filling_record import (
    ContainerFillingRecord, 
    ContainerFillingStatus
)
from domain.logistics.entities.container import Container
from domain.processing.repositories.container_tracking_repository import ContainerTrackingRepository


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
        self.repository = ContainerTrackingRepository(db_manager)
    
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
        if self.repository.is_container_in_use(container_id):
            raise ValueError(f"El contenedor ya está en uso en otro registro activo")
        
        now = datetime.now()
        
        record_data = {
            'container_id': container_id,
            'treatment_plant_id': treatment_plant_id,
            'fill_end_time': fill_end_time.isoformat(),
            'humidity': humidity,
            'ph_0h': ph_0h,
            'ph_0h_recorded_at': now.isoformat(),
            'status': ContainerFillingStatus.PENDING_PH.value,
            'notes': notes,
            'created_by': created_by,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        record_id = self.repository.create_filling_record(record_data)
        
        return self.repository.get_by_id(record_id)
    
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
        
        record = self.repository.get_by_id(record_id)
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
        
        self.repository.update_ph_measurement(
            record_id, 'ph_2h', ph_value, datetime.now()
        )
        
        return self.repository.get_by_id(record_id)
    
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
        
        record = self.repository.get_by_id(record_id)
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
        
        self.repository.update_ph_measurement(
            record_id, 'ph_24h', ph_value, datetime.now(),
            status=ContainerFillingStatus.READY_FOR_DISPATCH.value
        )
        
        return self.repository.get_by_id(record_id)
    
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
        
        record = self.repository.get_by_id(record_id)
        if not record:
            raise ValueError(f"Registro no encontrado: {record_id}")
        
        if record.status == ContainerFillingStatus.DISPATCHED.value:
            raise ValueError("Este contenedor ya fue despachado")
        
        self.repository.mark_as_dispatched(record_id, load_id, container_position)
        
        return self.repository.get_by_id(record_id)
    
    # --- Query Operations ---
    
    def get_filling_record_by_id(self, record_id: int) -> Optional[ContainerFillingRecord]:
        """Get a single filling record by ID with joined data."""
        return self.repository.get_by_id(record_id)
    
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
        return self.repository.get_active_records_by_plant(treatment_plant_id, status_filter)
    
    def get_records_ready_for_dispatch(
        self,
        treatment_plant_id: int
    ) -> List[ContainerFillingRecord]:
        """
        Get containers ready for dispatch from a treatment plant.
        These are containers with status READY_FOR_DISPATCH or FILLING
        (since container can leave while sample is kept for later pH measurements).
        """
        return self.repository.get_active_records_by_plant(
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
        return self.repository.get_dispatchable_records(treatment_plant_id)
    
    def get_available_containers(
        self,
        treatment_plant_id: Optional[int] = None
    ) -> List[Container]:
        """
        Get containers that are available for filling.
        Excludes containers that are already in use (IN_USE_TREATMENT status).
        """
        return self.repository.get_available_containers()
    
    def get_pending_ph_records(
        self,
        treatment_plant_id: int
    ) -> Dict[str, List[ContainerFillingRecord]]:
        """
        Get records with pending pH measurements, categorized by which pH is pending.
        
        Returns:
            Dict with keys 'pending_ph_2h' and 'pending_ph_24h'
        """
        records = self.repository.get_active_records_by_plant(treatment_plant_id)
        
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

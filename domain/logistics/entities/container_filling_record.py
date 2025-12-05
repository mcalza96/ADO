from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ContainerFillingStatus(Enum):
    """Status of a container filling record."""
    PENDING_PH = "PENDING_PH"  # Container filled, waiting for pH measurements
    READY_FOR_DISPATCH = "READY_FOR_DISPATCH"
    DISPATCHED = "DISPATCHED"
    
    # Legacy support for existing records
    FILLING = "FILLING"  # Deprecated, maps to PENDING_PH
    
    @property
    def display_name(self) -> str:
        names = {
            "PENDING_PH": "🧪 Pendiente pH",
            "FILLING": "🧪 Pendiente pH",  # Legacy support
            "READY_FOR_DISPATCH": "✅ Listo para Despacho",
            "DISPATCHED": "🚚 Despachado"
        }
        return names.get(self.value, self.value)


@dataclass
class ContainerFillingRecord:
    """
    Tracks container filling at treatment plant with pH measurements.
    
    Flow:
    1. Container is selected and starts filling (status=FILLING)
    2. When filling ends, operator records: fill_end_time, humidity, ph_0h
    3. After 2 hours, operator records ph_2h (system validates timing)
    4. After 24 hours, operator records ph_24h (system validates timing)
    5. Container becomes READY_FOR_DISPATCH
    6. When dispatched in logistics, status changes to DISPATCHED
    """
    id: Optional[int]
    container_id: int
    treatment_plant_id: int
    
    # Fill completion time
    fill_end_time: datetime
    
    # Initial measurements (required at creation)
    humidity: float  # 0-100%
    ph_0h: float  # 0-14
    ph_0h_recorded_at: Optional[datetime] = None
    
    # 2-hour pH measurement (recorded later)
    ph_2h: Optional[float] = None
    ph_2h_recorded_at: Optional[datetime] = None
    
    # 24-hour pH measurement (recorded later)
    ph_24h: Optional[float] = None
    ph_24h_recorded_at: Optional[datetime] = None
    
    # Status tracking
    status: str = ContainerFillingStatus.PENDING_PH.value
    
    # Dispatch tracking
    dispatched_load_id: Optional[int] = None
    dispatched_at: Optional[datetime] = None
    container_position: Optional[int] = None  # 1 or 2 when dispatched
    
    # Audit fields
    notes: Optional[str] = None
    created_by: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Joined fields (for display)
    container_code: Optional[str] = None
    treatment_plant_name: Optional[str] = None
    
    @property
    def display_status(self) -> str:
        """Returns formatted status for UI display."""
        try:
            return ContainerFillingStatus(self.status).display_name
        except ValueError:
            return self.status
    
    @property
    def can_record_ph_2h(self) -> bool:
        """
        Check if 2-hour pH can be recorded.
        Must be at least 2 hours after ph_0h was recorded.
        """
        if self.ph_2h is not None:
            return False  # Already recorded
        if self.ph_0h_recorded_at is None:
            return False
        
        elapsed = datetime.now() - self.ph_0h_recorded_at
        return elapsed.total_seconds() >= 2 * 3600  # 2 hours in seconds
    
    @property
    def can_record_ph_24h(self) -> bool:
        """
        Check if 24-hour pH can be recorded.
        Must be at least 24 hours after ph_0h was recorded.
        """
        if self.ph_24h is not None:
            return False  # Already recorded
        if self.ph_0h_recorded_at is None:
            return False
        
        elapsed = datetime.now() - self.ph_0h_recorded_at
        return elapsed.total_seconds() >= 24 * 3600  # 24 hours in seconds
    
    @property
    def time_until_ph_2h(self) -> Optional[float]:
        """Returns hours remaining until ph_2h can be recorded, or None if ready."""
        if self.ph_2h is not None or self.ph_0h_recorded_at is None:
            return None
        
        elapsed = datetime.now() - self.ph_0h_recorded_at
        remaining = (2 * 3600) - elapsed.total_seconds()
        return max(0, remaining / 3600)  # Return hours
    
    @property
    def time_until_ph_24h(self) -> Optional[float]:
        """Returns hours remaining until ph_24h can be recorded, or None if ready."""
        if self.ph_24h is not None or self.ph_0h_recorded_at is None:
            return None
        
        elapsed = datetime.now() - self.ph_0h_recorded_at
        remaining = (24 * 3600) - elapsed.total_seconds()
        return max(0, remaining / 3600)  # Return hours
    
    @property
    def is_complete(self) -> bool:
        """Check if all pH measurements have been recorded."""
        return all([
            self.ph_0h is not None,
            self.ph_2h is not None,
            self.ph_24h is not None
        ])
    
    def record_ph_2h(self, ph_value: float) -> bool:
        """
        Record the 2-hour pH measurement.
        Returns True if successful, False if timing constraint not met.
        """
        if not self.can_record_ph_2h:
            return False
        
        self.ph_2h = ph_value
        self.ph_2h_recorded_at = datetime.now()
        self.updated_at = datetime.now()
        return True
    
    def record_ph_24h(self, ph_value: float) -> bool:
        """
        Record the 24-hour pH measurement.
        Returns True if successful, False if timing constraint not met.
        """
        if not self.can_record_ph_24h:
            return False
        
        self.ph_24h = ph_value
        self.ph_24h_recorded_at = datetime.now()
        self.status = ContainerFillingStatus.READY_FOR_DISPATCH.value
        self.updated_at = datetime.now()
        return True
    
    def mark_as_dispatched(self, load_id: int, position: int) -> None:
        """Mark this container as dispatched on a specific load."""
        self.dispatched_load_id = load_id
        self.dispatched_at = datetime.now()
        self.container_position = position
        self.status = ContainerFillingStatus.DISPATCHED.value
        self.updated_at = datetime.now()


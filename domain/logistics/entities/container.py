from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ContainerStatus(Enum):
    """Container status enum."""
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"
    IN_USE_TREATMENT = "IN_USE_TREATMENT"  # Container is being filled at treatment plant
    
    @property
    def display_name(self) -> str:
        names = {
            "AVAILABLE": "✅ Disponible",
            "MAINTENANCE": "🔧 Mantenimiento",
            "DECOMMISSIONED": "❌ Fuera de Servicio",
            "IN_USE_TREATMENT": "🔄 En Llenado (Tratamiento)"
        }
        return names.get(self.value, self.value)


@dataclass
class Container:
    id: Optional[int]
    contractor_id: int
    code: str
    capacity_m3: float
    status: str = ContainerStatus.AVAILABLE.value  # 'AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED', 'IN_USE_TREATMENT'
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Joined fields (for display)
    contractor_name: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """
        Returns formatted name for UI dropdowns.
        Example: "TOLVA-204 (20m³)"
        """
        return f"{self.code} ({self.capacity_m3}m³)"
    
    @property
    def status_display(self) -> str:
        """Returns formatted status for UI display."""
        try:
            return ContainerStatus(self.status).display_name
        except ValueError:
            return self.status

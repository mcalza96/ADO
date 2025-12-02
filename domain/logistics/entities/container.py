from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Container:
    id: Optional[int]
    contractor_id: int
    code: str
    capacity_m3: float
    status: str = 'AVAILABLE'  # 'AVAILABLE', 'MAINTENANCE', 'DECOMMISSIONED'
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

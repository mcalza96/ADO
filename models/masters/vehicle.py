from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Vehicle:
    id: Optional[int]
    contractor_id: int
    license_plate: str
    tare_weight: float
    capacity_wet_tons: float
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    type: str = 'BATEA' # BATEA, AMPLIROLL
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Joined fields (for display only, not persisted)
    contractor_name: Optional[str] = field(default=None, compare=False)
    
    @property
    def max_capacity(self) -> float:
        """Alias for capacity_wet_tons for backward compatibility"""
        return self.capacity_wet_tons

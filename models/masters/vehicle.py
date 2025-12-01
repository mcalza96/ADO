from dataclasses import dataclass
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
    year: Optional[int] = None # Not in DB schema explicitly but in previous model, keeping for now or removing? Schema doesn't have year. I will keep it optional or remove if not in DB. Schema has brand, model. Previous model had year. I'll keep it but it won't be persisted unless I add column. Wait, schema.sql does NOT have year. I will remove it to match schema or add it to schema. Plan didn't mention year. I will remove it to be safe and consistent with schema.
    type: str = 'BATEA' # BATEA, AMPLIROLL - Not in schema explicitly? Schema doesn't have type. Previous model had it. I will remove it or add to schema. Schema has brand, model, license_plate, capacity, tare. No type. I will remove it.
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Joined fields (for display)
    contractor_name: Optional[str] = None

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class TreatmentPlant:
    id: Optional[int]
    client_id: int  # <--- FALTABA ESTO IMPRESCINDIBLE
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    authorization_resolution: Optional[str] = None
    allowed_vehicle_types: Optional[str] = None # Traido de Facility
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


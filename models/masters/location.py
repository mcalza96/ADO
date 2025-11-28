from dataclasses import dataclass
from typing import Optional

@dataclass
class Facility:
    id: Optional[int]
    client_id: int
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    allowed_vehicle_types: Optional[str] = None  # CSV: 'BATEA,AMPLIROLL' o None para ambos

@dataclass
class Site:
    id: Optional[int]
    name: str
    owner_name: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True

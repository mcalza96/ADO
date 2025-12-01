from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Plot:
    id: Optional[int]
    site_id: int
    name: str
    area_acres: float
    geometry_wkt: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Site:
    id: Optional[int]
    name: str
    owner_name: Optional[str] = None
    address_reference: Optional[str] = None
    region: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    plots: List[Plot] = field(default_factory=list)

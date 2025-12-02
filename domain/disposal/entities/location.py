from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class Plot:
    id: Optional[int]
    site_id: int
    name: str
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None
    nitrogen_limit_kg_per_ha: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    plots: List[Plot] = field(default_factory=list)

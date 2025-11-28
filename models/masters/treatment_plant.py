from dataclasses import dataclass
from typing import Optional

@dataclass
class TreatmentPlant:
    id: Optional[int]
    name: str
    address: Optional[str] = None
    authorization_resolution: Optional[str] = None # RCA/Resolution ID
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True

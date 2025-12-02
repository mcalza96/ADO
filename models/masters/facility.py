from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Facility:
    """
    Facility - Plantas/Instalaciones del Cliente (generadores).
    Estos son los orígenes donde se genera el residuo.
    """
    id: Optional[int]
    name: str
    client_id: Optional[int] = None  # Cliente dueño de la facilidad
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    allowed_vehicle_types: Optional[str] = None  # BATEA,AMPLIROLL
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

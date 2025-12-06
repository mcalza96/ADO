from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Facility:
    """
    Facility - Plantas/Instalaciones del Cliente (generadores).
    Estos son los orígenes donde se genera el residuo.
    
    Si is_link_point=True, la facility también puede actuar como punto de enlace
    intermedio en rutas (Origen -> Planta Enlace -> Destino Final).
    """
    id: Optional[int]
    name: str
    client_id: Optional[int] = None  # Cliente dueño de la facilidad
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    allowed_vehicle_types: Optional[str] = None  # BATEA,AMPLIROLL
    is_link_point: bool = False  # Si True, puede ser punto de enlace intermedio
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

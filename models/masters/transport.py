from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Contractor:
    id: Optional[int]
    name: str
    rut: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Driver:
    id: Optional[int]
    contractor_id: int
    name: str
    rut: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

@dataclass
class Vehicle:
    id: Optional[int]
    contractor_id: int
    license_plate: str
    tare_weight: float
    max_capacity: float
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    type: str = 'BATEA' # BATEA, AMPLIROLL
    is_active: bool = True

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Driver:
    id: Optional[int]
    contractor_id: int
    name: str
    rut: Optional[str] = None
    license_number: Optional[str] = None
    license_type: Optional[str] = None
    signature_image_path: Optional[str] = None
    # phone: Eliminado para coincidir con DB
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Joined fields
    contractor_name: Optional[str] = None

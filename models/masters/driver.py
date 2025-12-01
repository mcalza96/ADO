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
    phone: Optional[str] = None # Not in DB schema? Schema has license_number. Previous model had phone. Schema.sql for drivers: id, contractor_id, name, rut, license_number, license_type, signature_image_path, is_active. NO PHONE. I will remove phone.
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Joined fields
    contractor_name: Optional[str] = None

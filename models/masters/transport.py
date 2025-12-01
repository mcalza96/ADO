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
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Client:
    id: Optional[int]
    name: str
    rut: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    id: Optional[int]
    username: str
    email: str
    full_name: str
    role: str
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

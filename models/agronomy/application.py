from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class NitrogenApplication:
    id: Optional[int]
    site_id: int
    load_id: int
    nitrogen_applied_kg: float
    application_date: date

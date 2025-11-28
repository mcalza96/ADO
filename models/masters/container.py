from dataclasses import dataclass
from typing import Optional

@dataclass
class Container:
    id: Optional[int]
    code: str
    status: str = 'AVAILABLE' # AVAILABLE, IN_USE, MAINTENANCE
    current_plant_id: Optional[int] = None

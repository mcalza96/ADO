from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TreatmentBatch:
    id: Optional[int]
    facility_id: int  # Renamed from plant_id
    container_id: int
    fill_time: datetime
    ph_0h: float
    humidity: float
    ph_2h: Optional[float] = None
    ph_24h: Optional[float] = None
    status: str = 'MONITORING' # MONITORING, READY, DISPATCHED
    is_active: bool = True
    created_at: Optional[datetime] = None

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TreatmentBatch:
    id: Optional[int]
    plant_id: int
    container_id: int
    fill_time: datetime
    ph_0h: float
    humidity: float
    ph_2h: Optional[float] = None
    ph_24h: Optional[float] = None
    status: str = 'MONITORING' # MONITORING, READY, DISPATCHED
    created_at: Optional[datetime] = None

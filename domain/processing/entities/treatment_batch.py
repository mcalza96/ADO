from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

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
    
    # Flexible Attributes (JSONB-like storage)
    # Ejemplo: attributes = {'dosis_cal': 15.5, 'tiempo_mezclado_min': 45, 'operador': 'Juan Pérez'}
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    created_at: Optional[datetime] = None

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Dict, Any

@dataclass
class NitrogenApplication:
    id: Optional[int]
    site_id: int
    load_id: int
    nitrogen_applied_kg: float
    application_date: date
    
    # Flexible Attributes (JSONB-like storage)
    # Ejemplo: attributes = {'humedad_suelo': 12.5, 'velocidad_viento_kmh': 8, 'temperatura_ambiental': 22}
    attributes: Dict[str, Any] = field(default_factory=dict)

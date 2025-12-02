from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class RateSheet:
    """
    Tarifario para actividades.
    Ej: Transporte ($1000/km), Maquinaria ($50000/hora).
    """
    id: Optional[int]
    client_id: Optional[int] # Si es NULL, es tarifa base/default
    activity_type: str # 'TRANSPORTE', 'DISPOSICION', 'MAQUINARIA'
    
    unit_price: float
    unit_type: str # 'POR_KM', 'POR_TON', 'POR_HORA'
    
    currency: str = 'CLP'
    valid_from: datetime = None
    valid_to: Optional[datetime] = None

@dataclass
class CostRecord:
    """
    Registro de costo calculado para una operación específica.
    """
    id: Optional[int]
    related_entity_id: int # load_id o machine_log_id
    related_entity_type: str # 'LOAD' o 'MACHINE_LOG'
    
    amount: float
    currency: str = 'CLP'
    
    calculated_at: Optional[datetime] = None
    rate_sheet_id: Optional[int] = None # Trazabilidad de qué tarifa se usó

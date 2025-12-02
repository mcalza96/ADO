"""
StatusTransition Entity - Trazabilidad de Transiciones de Estado

Registra cada cambio de estado de una carga para:
- Auditoría completa
- Cálculo de tiempos en cada estado (SLA)
- Análisis de cuellos de botella
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class StatusTransition:
    """
    Representa una transición entre estados de una carga.
    
    Ejemplo:
        transition = StatusTransition(
            id=None,
            load_id=123,
            from_status="ASSIGNED",
            to_status="ACCEPTED",
            timestamp=datetime.now(),
            user_id=5,
            notes="Aceptado por conductor vía app móvil"
        )
    """
    id: Optional[int]
    load_id: int
    from_status: str           # Estado origen
    to_status: str             # Estado destino
    timestamp: datetime
    user_id: Optional[int] = None      # Usuario que realizó la transición
    notes: Optional[str] = None        # Notas adicionales (ej: razón de rechazo)
    
    def __post_init__(self):
        """Validaciones básicas al crear la transición"""
        if not self.load_id:
            raise ValueError("load_id is required")
        if not self.from_status or not self.to_status:
            raise ValueError("from_status and to_status are required")
        if not self.timestamp:
            raise ValueError("timestamp is required")
    
    @property
    def duration_since(self) -> float:
        """
        Retorna los segundos transcurridos desde esta transición.
        Útil para calcular tiempo en estado actual.
        """
        return (datetime.now() - self.timestamp).total_seconds()

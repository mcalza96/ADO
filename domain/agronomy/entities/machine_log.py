from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


@dataclass
class MachineLog:
    """
    Registro de trabajo de maquinaria pesada.
    
    Registra el uso de excavadoras, tractores, etc. para:
    - Trazabilidad de horas trabajadas
    - Base para mantenimiento preventivo
    - Costeo por sitio/actividad
    
    Example:
        >>> log = MachineLog(
        ...     id=None,
        ...     machine_id=5,
        ...     date=datetime.now(),
        ...     operator_id=10,
        ...     site_id=3,
        ...     start_hourmeter=Decimal('1000.5'),
        ...     end_hourmeter=Decimal('1008.5'),
        ...     activities=[{'task': 'Excavación', 'plot_id': 7}]
        ... )
        >>> print(log.total_hours)  # Decimal('8.0')
    """
    id: Optional[int]
    machine_id: int  # FK a vehicles (asset_type = HEAVY_EQUIPMENT)
    date: datetime
    operator_id: int  # FK a drivers/users
    site_id: int  # FK a sites
    
    start_hourmeter: Decimal  # Horómetro inicial (horas motor)
    end_hourmeter: Decimal  # Horómetro final
    
    # Calculado automáticamente
    total_hours: Optional[Decimal] = None
    
    # Actividades realizadas (JSON)
    # Ejemplo: [{'task': 'Excavación', 'plot_id': 5}, {'task': 'Nivelación', 'plot_id': 6}]
    activities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Audit
    created_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    
    def __post_init__(self):
        """Calcula total_hours automáticamente"""
        if self.start_hourmeter is not None and self.end_hourmeter is not None:
            self.total_hours = self.end_hourmeter - self.start_hourmeter

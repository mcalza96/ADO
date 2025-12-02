from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

class MaintenanceStrategy(str, Enum):
    BY_KM = "BY_KM"
    BY_HOURS = "BY_HOURS"

@dataclass
class MaintenancePlan:
    """
    Define un plan de mantenimiento preventivo para un activo.
    Ej: Cambio de Aceite cada 10,000 km.
    """
    id: Optional[int]
    asset_id: int  # FK a vehicles
    maintenance_type: str  # Ej: "Cambio de Aceite", "Revisión Frenos"
    frequency_value: float  # Ej: 10000 (km) o 250 (horas)
    strategy: MaintenanceStrategy  # BY_KM o BY_HOURS
    
    last_service_at_meter: float = 0.0  # Último valor del contador cuando se hizo servicio
    last_service_date: Optional[datetime] = None
    
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class MaintenanceOrder:
    """
    Orden de trabajo generada automáticamente cuando se cumple la frecuencia.
    """
    id: Optional[int]
    plan_id: int  # FK a maintenance_plans
    asset_id: int  # FK a vehicles (redundante pero útil para queries)
    
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    
    due_at_meter: float = 0.0  # A qué valor del contador le toca (ej: 150000)
    generated_at: datetime = None
    completed_at: Optional[datetime] = None
    
    notes: Optional[str] = None

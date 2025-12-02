from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    """
    Tipo de activo para clasificación de vehículos y maquinaria.
    
    ROAD_VEHICLE: Vehículos de transporte por carretera (camiones, etc.)
    HEAVY_EQUIPMENT: Maquinaria pesada (excavadoras, tractores, etc.)
    """
    ROAD_VEHICLE = "ROAD_VEHICLE"
    HEAVY_EQUIPMENT = "HEAVY_EQUIPMENT"


@dataclass
class Vehicle:
    id: Optional[int]
    contractor_id: int
    license_plate: str
    tare_weight: float
    capacity_wet_tons: float
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    type: str = 'BATEA' # BATEA, AMPLIROLL
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Asset Type Classification (added for Phase 1)
    asset_type: AssetType = AssetType.ROAD_VEHICLE
    
    # Dual Measurement Fields (added for Phase 1)
    # Para ROAD_VEHICLE: usar current_odometer (Kms)
    # Para HEAVY_EQUIPMENT: usar current_hourmeter (Horas Motor)
    current_odometer: Optional[int] = None  # Kilometraje actual
    current_hourmeter: Optional[float] = None  # Horómetro actual (horas motor)
    
    # Cost Base Fields (added for Phase 1)
    cost_per_km: Optional[float] = None  # Costo por kilómetro
    cost_per_hour: Optional[float] = None  # Costo por hora de operación
    
    # Joined fields (for display only, not persisted)
    contractor_name: Optional[str] = field(default=None, compare=False)
    
    @property
    def max_capacity(self) -> float:
        """Alias for capacity_wet_tons for backward compatibility"""
        return self.capacity_wet_tons


from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from domain.shared.enums import DisplayableEnum


class VehicleType(DisplayableEnum):
    """
    Tipo de vehículo de transporte de biosólidos.
    
    Define la capacidad de carga y compatibilidad con contenedores.
    - BATEA: Camión con tolva volcadora - carga directa, sin contenedores
    - AMPLIROLL: Porta-contenedor - trabaja con hasta 2 contenedores
    """
    BATEA = "BATEA"
    AMPLIROLL = "AMPLIROLL"
    
    @property
    def max_containers(self) -> int:
        """Cantidad máxima de contenedores que puede transportar."""
        return {
            VehicleType.BATEA: 0,      # No usa contenedores
            VehicleType.AMPLIROLL: 2   # Hasta 2 contenedores
        }.get(self, 1)
    
    @property
    def uses_containers(self) -> bool:
        """Indica si el vehículo trabaja con contenedores."""
        return self != VehicleType.BATEA
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        return {
            VehicleType.BATEA: "Batea (carga directa)",
            VehicleType.AMPLIROLL: "Ampliroll (contenedores)"
        }.get(self, self.value)


class AssetType(DisplayableEnum):
    """
    Tipo de activo para clasificación de vehículos y maquinaria.
    
    ROAD_VEHICLE: Vehículos de transporte por carretera (camiones, etc.)
    HEAVY_EQUIPMENT: Maquinaria pesada (excavadoras, tractores, etc.)
    """
    ROAD_VEHICLE = "ROAD_VEHICLE"
    HEAVY_EQUIPMENT = "HEAVY_EQUIPMENT"
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        return {
            AssetType.ROAD_VEHICLE: "Vehículo de Carretera",
            AssetType.HEAVY_EQUIPMENT: "Maquinaria Pesada"
        }.get(self, self.value)


@dataclass
class Vehicle:
    id: Optional[int]
    contractor_id: int
    license_plate: str
    tare_weight: float  # Peso del vehículo vacío (kg)
    max_gross_weight: float  # Peso Bruto Vehicular máximo permitido (kg)
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    type: str = VehicleType.BATEA.value  # BATEA, AMPLIROLL
    capacity_wet_tons: Optional[float] = None  # Calculado automáticamente
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
    
    def __post_init__(self):
        """Calcula capacity_wet_tons automáticamente si no está definido."""
        if self.capacity_wet_tons is None and self.max_gross_weight and self.tare_weight:
            self.capacity_wet_tons = (self.max_gross_weight - self.tare_weight) / 1000
    
    @property
    def max_capacity(self) -> float:
        """Capacidad máxima en kg (para validaciones de dispatch)."""
        return self.max_gross_weight - self.tare_weight
    
    @property
    def vehicle_type(self) -> VehicleType:
        """Returns the VehicleType enum for this vehicle."""
        try:
            return VehicleType(self.type)
        except ValueError:
            return VehicleType.BATEA


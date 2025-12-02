from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    origin_facility_id: int
    vehicle_id: int
    driver_id: int
    destination_site_id: int
    
    # Fields that might be missing in older records or specific flows
    manifest_code: Optional[str] = None
    contractor_id: Optional[int] = None
    destination_plot_id: Optional[int] = None
    
    # Optional/Nullable fields
    container_id: Optional[int] = None
    batch_id: Optional[int] = None # Legacy/Compatibility
    treatment_batch_id: Optional[int] = None # Link to operational batch
    origin_treatment_plant_id: Optional[int] = None
    destination_treatment_plant_id: Optional[int] = None
    
    # Operational Data
    material_class: Optional[str] = None
    guide_number: Optional[str] = None  # Guía de despacho
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    weight_net: Optional[float] = None  # Alias for net_weight (backward compatibility)
    weight_gross_reception: Optional[float] = None  # Peso bruto en recepción
    
    # Status and Timing
    status: str = 'CREATED'
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
    # Flexible Attributes (JSONB-like storage)
    # Permite almacenar datos variables sin cambiar el schema:
    # Ejemplo: attributes = {'ph_inicial': 7.5, 'temperatura_llegada': 25.3, 'odometro_inicio': 145230}
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None

    def calculate_net_weight(self) -> None:
        """
        Updates the net_weight if gross_weight and tare_weight are present.
        """
        if self.gross_weight is not None and self.tare_weight is not None:
            self.net_weight = self.gross_weight - self.tare_weight

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    manifest_code: Optional[str]
    origin_facility_id: int
    contractor_id: int
    vehicle_id: int
    driver_id: int
    destination_site_id: int
    destination_plot_id: int
    
    # Optional/Nullable fields
    container_id: Optional[int] = None
    batch_id: Optional[int] = None # Legacy/Compatibility
    treatment_batch_id: Optional[int] = None # Link to operational batch
    
    # Operational Data
    material_class: Optional[str] = None
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    
    # Status and Timing
    status: str = 'CREATED'
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
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

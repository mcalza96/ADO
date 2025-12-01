from dataclasses import dataclass
from typing import Optional
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
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    
    # Status and Timing
    status: str = 'CREATED'
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
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

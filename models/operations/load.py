from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    origin_facility_id: int
    # Optional fields for Request phase
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    destination_site_id: Optional[int] = None
    batch_id: Optional[int] = None
    
    # Execution details
    ticket_number: Optional[str] = None
    guide_number: Optional[str] = None
    weight_gross: Optional[float] = None
    weight_tare: Optional[float] = None
    weight_net: Optional[float] = None
    
    status: str = 'Requested'
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

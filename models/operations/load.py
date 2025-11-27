from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    driver_id: int
    vehicle_id: int
    origin_facility_id: int
    destination_site_id: int
    batch_id: Optional[int]
    ticket_number: Optional[str] = None
    weight_gross: Optional[float] = None
    weight_tare: Optional[float] = None
    weight_net: Optional[float] = None
    status: str = 'Scheduled'
    scheduled_date: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

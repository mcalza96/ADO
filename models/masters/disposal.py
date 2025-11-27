from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Plot:
    id: Optional[int]
    site_id: int
    name: str
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None
    is_active: bool = True

@dataclass
class SoilSample:
    id: Optional[int]
    plot_id: int
    sampling_date: date
    nitrogen_current: Optional[float] = None
    phosphorus_current: Optional[float] = None
    potassium_current: Optional[float] = None
    ph_level: Optional[float] = None
    heavy_metals_limit_json: Optional[str] = None
    valid_until: Optional[date] = None
    created_at: Optional[datetime] = None

@dataclass
class Application:
    id: Optional[int]
    plot_id: int
    application_date: date
    total_tonnage_applied: Optional[float] = None
    nitrogen_load_applied: Optional[float] = None
    batch_source_ids: Optional[str] = None
    notes: Optional[str] = None

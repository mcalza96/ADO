from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Batch:
    id: Optional[int]
    facility_id: int
    batch_code: str
    production_date: date
    sludge_type: Optional[str] = None
    class_type: Optional[str] = None
    initial_tonnage: Optional[float] = None
    status: str = 'Open'
    created_at: Optional[datetime] = None

@dataclass
class LabResult:
    id: Optional[int]
    batch_id: int
    sample_date: date
    ph: Optional[float] = None
    humidity_percentage: Optional[float] = None
    dry_matter_percentage: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    heavy_metals_json: Optional[str] = None
    coliforms: Optional[float] = None
    salmonella_presence: Optional[bool] = None
    created_at: Optional[datetime] = None

from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Batch:
    id: Optional[int]
    facility_id: int
    batch_code: str
    production_date: date
    initial_tonnage: Optional[float] = None
    current_tonnage: Optional[float] = None  # Available stock for dispatch
    sludge_type: Optional[str] = None
    class_type: Optional[str] = None  # 'A', 'B', 'NoClass'
    status: str = 'Available'  # Available, Depleted, Quarantined
    
    # Nutrient Analysis (for PAN calculation and compliance)
    nitrate_no3: Optional[float] = None  # mg/kg dry weight
    ammonium_nh4: Optional[float] = None  # mg/kg dry weight
    tkn: Optional[float] = None  # Total Kjeldahl Nitrogen mg/kg
    percent_solids: Optional[float] = None  # % Dry Matter (0-100)
    
    # Heavy Metals (JSON string serialized from MetalAnalysisDTO)
    heavy_metals_json: Optional[str] = None
    
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

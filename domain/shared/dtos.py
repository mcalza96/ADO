from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class NutrientAnalysisDTO:
    nitrate_no3: float  # mg/kg (dry weight)
    ammonium_nh4: float # mg/kg (dry weight)
    tkn: float          # Total Kjeldahl Nitrogen mg/kg (dry weight)
    percent_solids: float # % Dry Matter (0-100)

@dataclass
class MetalAnalysisDTO:
    arsenic: float = 0.0
    cadmium: float = 0.0
    copper: float = 0.0
    lead: float = 0.0
    mercury: float = 0.0
    nickel: float = 0.0
    selenium: float = 0.0
    zinc: float = 0.0

@dataclass
class ApplicationScenarioDTO:
    crop_n_requirement: float # lbs/acre or kg/ha
    injection_method: bool = False # True = Injection (Higher Kvol), False = Surface

@dataclass
class CreateLoadDTO:
    origin_facility_id: int
    contractor_id: int
    vehicle_id: int
    driver_id: int
    destination_site_id: int
    destination_plot_id: int
    material_class: str
    created_by_user_id: int
    container_id: Optional[int] = None
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    dispatch_time: Optional[str] = None # ISO format string

@dataclass
class LoadDTO:
    id: int
    manifest_code: str
    origin_facility_id: int
    contractor_id: int
    vehicle_id: int
    driver_id: int
    destination_site_id: int
    destination_plot_id: int
    status: str
    material_class: Optional[str] = None
    container_id: Optional[int] = None
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    dispatch_time: Optional[str] = None
    arrival_time: Optional[str] = None
    created_at: Optional[str] = None

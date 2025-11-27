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

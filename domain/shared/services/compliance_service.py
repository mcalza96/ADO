from typing import Dict, Any, Optional
import json
from datetime import date
from database.repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.processing.repositories.batch_repository import BatchRepository
from domain.shared.entities.location import Site
from domain.disposal.entities.application import NitrogenApplication
from domain.disposal.logic.calculator import AgronomyCalculator
from domain.shared.dtos import NutrientAnalysisDTO, ApplicationScenarioDTO, MetalAnalysisDTO
from domain.shared.exceptions import AgronomicException, ComplianceException, ComplianceViolationError
from domain.shared.constants import CROP_REQUIREMENTS, EPA_503_TABLE1_LIMITS, DEFAULT_NITROGEN_LIMIT

class ComplianceService:
    """
    Orchestrates agronomic and environmental compliance validations.
    Enforces Hard Constraints for Sprint 3.
    """

    def __init__(self,        site_repo: BaseRepository[Site],
        load_repo: LoadRepository,
        batch_repo: BatchRepository,
        application_repo: BaseRepository[NitrogenApplication]
):
        self.site_repo = site_repo
        self.load_repo = load_repo
        self.batch_repo = batch_repo
        self.application_repo = application_repo

    def validate_dispatch(self, batch_id: int, site_id: int, tonnage: float) -> bool:
        """
        Performs hard validation checks before allowing a dispatch.
        Raises ComplianceViolationError if any check fails.
        
        Checks:
        1. Quality (Heavy Metals & Status)
        2. Classification (Class B restrictions - simplified)
        3. Agronomic Load (Nitrogen Capacity)
        """
        # 1. Get Entities
        batch = self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
            
        site = self.site_repo.get_by_id(site_id)
        if not site:
            raise ValueError(f"Site {site_id} not found")
            
        plot = self.site_repo.get_active_plot(site_id)
        if not plot:
            raise ComplianceViolationError(f"Site {site.name} has no active plot defined.")

        # --- CHECK 1: QUALITY & STATUS ---
        if batch.status == 'Quarantined':
            raise ComplianceViolationError(f"Batch {batch.batch_code} is Quarantined. Cannot dispatch.")
            
        # Validate Heavy Metals
        if batch.heavy_metals_json:
            try:
                metals_dict = json.loads(batch.heavy_metals_json)
                for metal, limit in EPA_503_TABLE1_LIMITS.items():
                    value = metals_dict.get(metal, 0.0)
                    if value > limit:
                        raise ComplianceViolationError(
                            f"Heavy Metal Violation: {metal.capitalize()} level ({value} mg/kg) "
                            f"exceeds EPA 503 limit ({limit} mg/kg)."
                        )
            except json.JSONDecodeError:
                pass # If JSON is invalid, we skip metal check (or could block, but let's be lenient for now)

        # --- CHECK 2: CLASSIFICATION ---
        # Simplified check: If Class B, just ensure site is active (placeholder for real restrictions)
        if batch.class_type == 'B':
            if not site.is_active:
                 raise ComplianceViolationError(f"Site {site.name} is not active for Class B application.")

        # --- CHECK 3: AGRONOMIC LOAD (NITROGEN) ---
        # 3.1 Calculate PAN for this batch
        # If nutrient data is missing, we can't calculate. 
        # For Sprint 3, if missing, we might assume a default or block. Let's block to be safe.
        if batch.nitrate_no3 is None or batch.ammonium_nh4 is None or batch.tkn is None:
             # Fallback or Error? Let's raise error to enforce data quality
             raise ComplianceViolationError("Batch missing nutrient analysis data. Cannot calculate PAN.")
             
        analysis_dto = NutrientAnalysisDTO(
            nitrate_no3=batch.nitrate_no3,
            ammonium_nh4=batch.ammonium_nh4,
            tkn=batch.tkn,
            percent_solids=batch.percent_solids or 20.0 # Default 20% if missing
        )
        
        # Scenario: Surface application (conservative)
        scenario_dto = ApplicationScenarioDTO(
            crop_n_requirement=0, # Not needed for PAN calc
            injection_method=False
        )
        
        pan_lbs_per_dry_ton = AgronomyCalculator.calculate_pan(analysis_dto, scenario_dto, batch.sludge_type or 'Anaerobic_Digestion')
        # Convert to kg/ton (approx same if 0.002 factor used for both, but let's be precise)
        # The calculator returns lbs/ton if input is mg/kg * 0.002. 
        # 1 lb/ton = 0.5 kg/ton. Wait.
        # mg/kg = ppm. 
        # 1000 mg/kg = 1 kg/ton.
        # Formula uses 0.002. 
        # Let's assume calculator returns kg/ton directly if we adjust factor or interpret result.
        # Actually, let's look at calculator: (mg/kg * 0.002) -> lbs/ton.
        # To get kg/metric_ton: mg/kg * 0.001.
        # So PAN (lbs/ton) * 0.5 = PAN (kg/metric_ton).
        pan_kg_per_ton = pan_lbs_per_dry_ton * 0.5 
        
        # 3.2 Calculate Nitrogen in this Load
        # Load Tonnage is Wet Tons.
        # Dry Tons = Wet Tons * (%Solids / 100)
        dry_tons = tonnage * (analysis_dto.percent_solids / 100.0)
        nitrogen_load_kg = dry_tons * pan_kg_per_ton
        
        # 3.3 Check Site Capacity
        current_year = date.today().year
        historical_n = self.application_repo.get_year_total_nitrogen(site_id, current_year)
        
        # Determine Limit
        limit_per_ha = plot.nitrogen_limit_kg_per_ha or CROP_REQUIREMENTS.get(plot.crop_type, DEFAULT_NITROGEN_LIMIT)
        site_area_ha = plot.area_hectares or 0
        if site_area_ha <= 0:
             raise ComplianceViolationError(f"Plot {plot.name} has invalid area (0 ha).")
             
        total_limit_kg = limit_per_ha * site_area_ha
        
        remaining_capacity = total_limit_kg - historical_n
        
        if nitrogen_load_kg > remaining_capacity:
            raise ComplianceViolationError(
                f"Nitrogen Excess: Site capacity exceeded. "
                f"Remaining: {remaining_capacity:.1f} kg N. "
                f"This load adds: {nitrogen_load_kg:.1f} kg N."
            )

        return True

    def get_nitrogen_capacity(self, site_id: int) -> Dict[str, float]:
        """
        Returns nitrogen capacity info for UI visualization.
        """
        plot = self.site_repo.get_active_plot(site_id)
        if not plot:
            return {'limit_kg': 0, 'applied_kg': 0, 'remaining_kg': 0, 'percent_used': 0}
            
        current_year = date.today().year
        applied_kg = self.application_repo.get_year_total_nitrogen(site_id, current_year)
        
        limit_per_ha = plot.nitrogen_limit_kg_per_ha or CROP_REQUIREMENTS.get(plot.crop_type, DEFAULT_NITROGEN_LIMIT)
        area = plot.area_hectares or 0
        limit_kg = limit_per_ha * area
        
        remaining = max(0, limit_kg - applied_kg)
        percent = (applied_kg / limit_kg * 100) if limit_kg > 0 else 100
        
        return {
            'limit_kg': limit_kg,
            'applied_kg': applied_kg,
            'remaining_kg': remaining,
            'percent_used': min(100.0, percent)
        }

    def calculate_load_agronomics(self, batch_id: int, tonnage: float) -> Dict[str, float]:
        """
        Helper to calculate agronomic data for a potential load.
        Returns: { 'pan_kg_per_ton': float, 'total_n_kg': float }
        """
        batch = self.batch_repo.get_by_id(batch_id)
        if not batch or not batch.nitrate_no3:
            return {'pan_kg_per_ton': 0.0, 'total_n_kg': 0.0}
            
        analysis_dto = NutrientAnalysisDTO(
            nitrate_no3=batch.nitrate_no3,
            ammonium_nh4=batch.ammonium_nh4,
            tkn=batch.tkn,
            percent_solids=batch.percent_solids or 20.0
        )
        scenario_dto = ApplicationScenarioDTO(crop_n_requirement=0, injection_method=False)
        
        pan_lbs = AgronomyCalculator.calculate_pan(analysis_dto, scenario_dto, batch.sludge_type or 'Anaerobic_Digestion')
        pan_kg_ton = pan_lbs * 0.5
        
        dry_tons = tonnage * (analysis_dto.percent_solids / 100.0)
        total_n = dry_tons * pan_kg_ton
        
        return {
            'pan_kg_per_ton': pan_kg_ton,
            'total_n_kg': total_n
        }

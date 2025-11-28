from typing import Dict, Any
from repositories.site_repository import SiteRepository
from repositories.load_repository import LoadRepository
from domain.agronomy.calculator import AgronomyCalculator
from domain.dtos import NutrientAnalysisDTO, ApplicationScenarioDTO
from domain.exceptions import AgronomicException, ComplianceException

class ComplianceService:
    """
    Orchestrates agronomic and environmental compliance validations.
    """
    
    # Placeholder for Crop Nitrogen Requirements (e.g., lbs/acre or kg/ha)
    # Assuming units match the output of AgronomyCalculator (e.g., lbs/acre)
    CROP_REQUIREMENTS = {
        'Corn': 200.0,
        'Wheat': 150.0,
        'Soybean': 0.0, # Legume, fixes own N
        'Hay': 100.0,
        'Pasture': 80.0
    }

    def __init__(self, site_repo: SiteRepository, load_repo: LoadRepository):
        self.site_repo = site_repo
        self.load_repo = load_repo

    def validate_application_feasibility(self, site_id: int, volume_tons: float, batch_analysis: Dict[str, Any]) -> bool:
        """
        Validates if applying the given volume to the site is agronomically feasible.
        Raises AgronomicException or ComplianceException if not.
        """
        # 1. Get Site and Active Plot
        plot = self.site_repo.get_active_plot(site_id)
        if not plot:
            raise ComplianceException(f"No active plot found for Site ID {site_id}. Cannot schedule application.")
        
        if not plot.crop_type:
            raise AgronomicException(f"Plot {plot.name} has no crop assigned. Cannot calculate N requirements.")

        # 2. Prepare Data for Calculation
        # Map dictionary to DTO
        try:
            analysis_dto = NutrientAnalysisDTO(
                nitrate_no3=batch_analysis.get('nitrate_no3', 0.0),
                ammonium_nh4=batch_analysis.get('ammonium_nh4', 0.0),
                tkn=batch_analysis.get('tkn', 0.0),
                percent_solids=batch_analysis.get('percent_solids', 0.0)
            )
        except Exception as e:
             raise AgronomicException(f"Invalid batch analysis data: {str(e)}")

        # 4. Determine Crop Requirement (Moved up)
        crop_req = self.CROP_REQUIREMENTS.get(plot.crop_type, 150.0) # Default to 150 if unknown

        # Default scenario for now (could be passed in if needed)
        scenario_dto = ApplicationScenarioDTO(
            crop_n_requirement=crop_req,
            injection_method=False # Default to surface application
        )

        # 3. Calculate PAN (Plant Available Nitrogen)
        # Result in lbs/dry_ton (assuming calculator uses 0.002 factor for mg/kg -> lbs/ton)
        pan = AgronomyCalculator.calculate_pan(analysis_dto, scenario_dto)

        # 5. Calculate Max Application Rate (Dry Tons per Acre)
        try:
            max_rate_dry_tons_per_acre = AgronomyCalculator.calculate_max_application_rate(pan, crop_req)
        except AgronomicException as e:
            raise AgronomicException(f"Calculation Error: {str(e)}")

        # 6. Convert Rate to Total Volume Allowed (Wet Tons) for the Plot
        # Need Plot Area. Assuming plot.area_hectares is available.
        if not plot.area_hectares or plot.area_hectares <= 0:
             raise AgronomicException(f"Plot {plot.name} has invalid area. Cannot calculate capacity.")
        
        # Convert Hectares to Acres (1 Ha = 2.47105 Acres)
        area_acres = plot.area_hectares * 2.47105
        
        max_total_dry_tons = max_rate_dry_tons_per_acre * area_acres
        
        # Convert Max Dry Tons to Max Wet Tons
        # Wet = Dry / (%Solids/100)
        try:
            max_total_wet_tons = AgronomyCalculator.convert_to_wet_tons(max_total_dry_tons, analysis_dto.percent_solids)
        except AgronomicException as e:
             raise AgronomicException(f"Conversion Error: {str(e)}")

        # 7. Validate
        # Note: This checks if the *single load* exceeds the *entire plot capacity*.
        # Realistically, we should check (Current Cumulative + Load) > Max.
        # But per instructions: "Comparar: Si volume_tons > max_allowed"
        # I will implement the check as requested, but ideally we'd query past applications.
        # For this task, I'll stick to the prompt's scope but add a TODO.
        
        # TODO: Subtract already applied volume from max_total_wet_tons
        
        if volume_tons > max_total_wet_tons:
            raise AgronomicException(
                f"Exceso de Nitrógeno: Intenta aplicar {volume_tons:.2f} tons, "
                f"pero el máximo permitido para {plot.crop_type} en este sitio es {max_total_wet_tons:.2f} tons."
            )

        return True

from typing import Dict, Any, Optional
import json
from datetime import date
from database.repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
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

    def __init__(self, site_repo: BaseRepository[Site],
        load_repo: LoadRepository,
        application_repo: BaseRepository[NitrogenApplication]
    ):
        self.site_repo = site_repo
        self.load_repo = load_repo
        self.application_repo = application_repo

    def validate_dispatch(self, site_id: int, tonnage: float) -> bool:
        """
        Performs hard validation checks before allowing a dispatch.
        Raises ComplianceViolationError if any check fails.
        
        Checks:
        1. Site and Plot existence
        2. Agronomic Load (Nitrogen Capacity) - simplified without batch data
        """
        site = self.site_repo.get_by_id(site_id)
        if not site:
            raise ValueError(f"Site {site_id} not found")
            
        plot = self.site_repo.get_active_plot(site_id)
        if not plot:
            raise ComplianceViolationError(f"Site {site.name} has no active plot defined.")

        # Check Site Capacity (simplified - uses default nitrogen values)
        current_year = date.today().year
        historical_n = self.application_repo.get_year_total_nitrogen(site_id, current_year)
        
        # Determine Limit
        limit_per_ha = plot.nitrogen_limit_kg_per_ha or CROP_REQUIREMENTS.get(plot.crop_type, DEFAULT_NITROGEN_LIMIT)
        site_area_ha = plot.area_hectares or 0
        if site_area_ha <= 0:
             raise ComplianceViolationError(f"Plot {plot.name} has invalid area (0 ha).")
             
        total_limit_kg = limit_per_ha * site_area_ha
        remaining_capacity = total_limit_kg - historical_n
        
        # Estimate nitrogen from tonnage (using default PAN value)
        default_pan_kg_per_ton = 5.0  # Conservative default
        estimated_n_kg = tonnage * default_pan_kg_per_ton
        
        if estimated_n_kg > remaining_capacity:
            raise ComplianceViolationError(
                f"Nitrogen Excess: Site capacity may be exceeded. "
                f"Remaining: {remaining_capacity:.1f} kg N. "
                f"Estimated load: {estimated_n_kg:.1f} kg N."
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

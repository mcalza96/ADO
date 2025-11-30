from domain.dtos import NutrientAnalysisDTO, ApplicationScenarioDTO
from domain.exceptions import AgronomicException
from domain.constants import K_MIN_DEFAULTS, UNIT_CONVERSION_FACTOR

class AgronomyCalculator:
    """
    Domain Service for Agronomic Calculations (EPA 503).
    """
    
    @staticmethod
    def calculate_pan(analysis: NutrientAnalysisDTO, scenario: ApplicationScenarioDTO, sludge_type: str = 'Anaerobic_Digestion') -> float:
        """
        Calculates Plant Available Nitrogen (PAN) in lbs/dry_ton (or kg/dry_ton depending on input units).
        Formula: PAN = (NO3 * 0.002) + Kvol(NH4 * 0.002) + Kmin(Norg * 0.002)
        Where 0.002 converts mg/kg to lbs/dry_ton.
        """
        # 1. Determine Factors
        # Kvol: Volatilization factor. 1.0 if injected (no loss), ~0.5-0.7 if surface applied.
        k_vol = 1.0 if scenario.injection_method else 0.5
        
        # Kmin: Mineralization factor based on sludge type
        k_min = K_MIN_DEFAULTS.get(sludge_type, 0.20)

        # 2. Calculate Organic Nitrogen
        # Norg = TKN - NH4
        n_org = max(0, analysis.tkn - analysis.ammonium_nh4)

        # 3. Apply Formula
        # We assume inputs are in mg/kg. The factor 0.002 converts to lbs/ton.
        # If inputs were %, factor would be 20.
        # Let's stick to the prompt's formula structure implying mg/kg inputs.
        
        term_no3 = analysis.nitrate_no3 * UNIT_CONVERSION_FACTOR
        term_nh4 = k_vol * (analysis.ammonium_nh4 * UNIT_CONVERSION_FACTOR)
        term_norg = k_min * (n_org * UNIT_CONVERSION_FACTOR)
        
        pan = term_no3 + term_nh4 + term_norg
        return pan

    @staticmethod
    def calculate_max_application_rate(pan: float, crop_requirement: float) -> float:
        """
        Calculates the maximum application rate in Dry Tons per Acre/Hectare.
        Rate = Crop Requirement / PAN
        """
        if pan <= 0:
            raise AgronomicException("Calculated PAN is zero or negative. Cannot determine application rate.")
        
        return crop_requirement / pan

    @staticmethod
    def convert_to_wet_tons(dry_tons: float, percent_solids: float) -> float:
        """
        Converts Dry Tons to Wet Tons.
        Wet Tons = Dry Tons / (Percent Solids / 100)
        """
        if percent_solids <= 0:
            raise AgronomicException("Percent solids must be greater than 0.")
        
        return dry_tons / (percent_solids / 100.0)

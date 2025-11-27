from domain.dtos import MetalAnalysisDTO
from domain.exceptions import ComplianceException
from domain.compliance.constants import EPA_CEILING_LIMITS, RESTRICTED_SITE_TYPES

class ComplianceValidator:
    """
    Domain Service for Regulatory Compliance Validation.
    """

    @staticmethod
    def validate_heavy_metals(analysis: MetalAnalysisDTO):
        """
        Validates if the metal analysis exceeds EPA Ceiling Concentrations.
        Raises ComplianceException if any limit is exceeded.
        """
        violations = []
        
        # Check each metal
        if analysis.arsenic > EPA_CEILING_LIMITS['arsenic']:
            violations.append(f"Arsenic ({analysis.arsenic}) exceeds limit ({EPA_CEILING_LIMITS['arsenic']})")
            
        if analysis.cadmium > EPA_CEILING_LIMITS['cadmium']:
            violations.append(f"Cadmium ({analysis.cadmium}) exceeds limit ({EPA_CEILING_LIMITS['cadmium']})")
            
        if analysis.copper > EPA_CEILING_LIMITS['copper']:
            violations.append(f"Copper ({analysis.copper}) exceeds limit ({EPA_CEILING_LIMITS['copper']})")
            
        if analysis.lead > EPA_CEILING_LIMITS['lead']:
            violations.append(f"Lead ({analysis.lead}) exceeds limit ({EPA_CEILING_LIMITS['lead']})")
            
        if analysis.mercury > EPA_CEILING_LIMITS['mercury']:
            violations.append(f"Mercury ({analysis.mercury}) exceeds limit ({EPA_CEILING_LIMITS['mercury']})")
            
        if analysis.nickel > EPA_CEILING_LIMITS['nickel']:
            violations.append(f"Nickel ({analysis.nickel}) exceeds limit ({EPA_CEILING_LIMITS['nickel']})")
            
        if analysis.selenium > EPA_CEILING_LIMITS['selenium']:
            violations.append(f"Selenium ({analysis.selenium}) exceeds limit ({EPA_CEILING_LIMITS['selenium']})")
            
        if analysis.zinc > EPA_CEILING_LIMITS['zinc']:
            violations.append(f"Zinc ({analysis.zinc}) exceeds limit ({EPA_CEILING_LIMITS['zinc']})")

        if violations:
            raise ComplianceException("Heavy Metal Ceiling Concentration Exceeded: " + "; ".join(violations))
        
        return True

    @staticmethod
    def validate_class_restrictions(biosolid_class: str, site_type: str):
        """
        Validates if the biosolid class is allowed for the destination site type.
        Class B cannot be applied to restricted public access sites.
        """
        if biosolid_class == 'B' and site_type in RESTRICTED_SITE_TYPES:
            raise ComplianceException(f"Class B Biosolids cannot be applied to restricted site type: {site_type}")
        
        return True

from domain.shared.dtos import MetalAnalysisDTO
from domain.shared.exceptions import ComplianceException
from domain.shared.constants import EPA_CEILING_LIMITS, RESTRICTED_SITE_TYPES

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
        
        # Check each metal dynamically
        for metal, limit in EPA_CEILING_LIMITS.items():
            # Get the value from the DTO using getattr. 
            # We assume the DTO fields match the keys in EPA_CEILING_LIMITS (lowercase).
            # If DTO fields are different, we might need a mapping.
            # Based on previous code: 'arsenic', 'cadmium', etc. match DTO fields.
            value = getattr(analysis, metal, None)
            
            if value is not None and value > limit:
                violations.append(f"{metal.capitalize()} ({value}) exceeds limit ({limit})")

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

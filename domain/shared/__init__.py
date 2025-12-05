"""
Shared Domain Module - Componentes compartidos entre todos los subdominios.

Exporta enums, excepciones, DTOs, services base y constantes comunes.
"""

# Enums
from .enums import DisplayableEnum

# Exceptions
from .exceptions import (
    DomainException,
    ComplianceException,
    AgronomicException,
    LogisticsException,
    TransitionException,
    ComplianceViolationError,
)

# DTOs
from .dtos import (
    NutrientAnalysisDTO,
    MetalAnalysisDTO,
    ApplicationScenarioDTO,
    CreateLoadDTO,
    LoadDTO,
    AssignmentRequest,
)

# Base Services
from .base_service import BaseService
from .generic_crud_service import GenericCrudService

# Constants
from .constants import (
    K_MIN_DEFAULTS,
    UNIT_CONVERSION_FACTOR,
    SLUDGE_DENSITY,
    CROP_REQUIREMENTS,
    EPA_503_TABLE1_LIMITS,
    EPA_CEILING_LIMITS,
    RESTRICTED_SITE_TYPES,
    DEFAULT_NITROGEN_LIMIT,
)

__all__ = [
    # Enums
    'DisplayableEnum',
    # Exceptions
    'DomainException',
    'ComplianceException',
    'AgronomicException',
    'LogisticsException',
    'TransitionException',
    'ComplianceViolationError',
    # DTOs
    'NutrientAnalysisDTO',
    'MetalAnalysisDTO',
    'ApplicationScenarioDTO',
    'CreateLoadDTO',
    'LoadDTO',
    'AssignmentRequest',
    # Base Services
    'BaseService',
    'GenericCrudService',
    # Constants
    'K_MIN_DEFAULTS',
    'UNIT_CONVERSION_FACTOR',
    'SLUDGE_DENSITY',
    'CROP_REQUIREMENTS',
    'EPA_503_TABLE1_LIMITS',
    'EPA_CEILING_LIMITS',
    'RESTRICTED_SITE_TYPES',
    'DEFAULT_NITROGEN_LIMIT',
]
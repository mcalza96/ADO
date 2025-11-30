class DomainException(Exception):
    """Base class for all domain exceptions."""
    pass

class ComplianceException(DomainException):
    """Raised when a compliance rule is violated (e.g. Heavy Metals)."""
    pass

class AgronomicException(DomainException):
    """Raised when an agronomic rule is violated (e.g. Application Rate)."""
    pass

class LogisticsException(DomainException):
    """Raised when a logistics rule is violated (e.g. Overweight)."""
    pass

class TransitionException(DomainException):
    """Raised when an invalid state transition is attempted."""
    pass

class ComplianceViolationError(ComplianceException):
    """Raised when a dispatch is blocked due to compliance violations (hard constraints)."""
    pass

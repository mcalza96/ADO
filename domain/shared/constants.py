# Mineralization Rates (Kmin) - Simplified defaults
K_MIN_DEFAULTS = {
    'Compost': 0.10,
    'Anaerobic_Digestion': 0.20,
    'Aerobic_Digestion': 0.30,
    'Raw': 0.30
}

# Conversion factor from mg/kg to lbs/ton
UNIT_CONVERSION_FACTOR = 0.002

# Default Sludge Density (tons/m3) for capacity checks
SLUDGE_DENSITY = 1.2

# Crop Nitrogen Requirements (kg/ha) - Standardized to Metric for Chile
CROP_REQUIREMENTS = {
    'Corn': 200.0,
    'Wheat': 150.0,
    'Soybean': 0.0, # Legume, fixes own N
    'Hay': 100.0,
    'Pasture': 80.0
}

# EPA 503 Table 1 - Ceiling Concentrations for Heavy Metals (mg/kg dry weight)
EPA_503_TABLE1_LIMITS = {
    'arsenic': 75.0,
    'cadmium': 85.0,
    'copper': 4300.0,
    'lead': 840.0,
    'mercury': 57.0,
    'nickel': 420.0,
    'selenium': 100.0,
    'zinc': 7500.0
}

# Default nitrogen application limit if not specified by site (kg N/ha/year)
DEFAULT_NITROGEN_LIMIT = 200.0

from enum import Enum

class TaskPriority(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

# LoadStatus is now in domain.logistics.entities.load_status
# Import from there instead of using this deprecated version

class Role(Enum):
    DRIVER = "Driver"
    ADMIN = "Admin"
    OPERATOR = "Operator"
    LAB_TECH = "LabTech"
    DISPATCHER = "Dispatcher"



# Mineralization Rates (Kmin) - Simplified defaults
K_MIN_DEFAULTS = {
    'Compost': 0.10,
    'Anaerobic_Digestion': 0.20,
    'Aerobic_Digestion': 0.30,
    'Raw': 0.30
}

# Conversion factor from mg/kg to lbs/ton
UNIT_CONVERSION_FACTOR = 0.002

# Crop Nitrogen Requirements (e.g., lbs/acre or kg/ha)
CROP_REQUIREMENTS = {
    'Corn': 200.0,
    'Wheat': 150.0,
    'Soybean': 0.0, # Legume, fixes own N
    'Hay': 100.0,
    'Pasture': 80.0
}

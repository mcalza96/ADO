from domain.dtos import NutrientAnalysisDTO, ApplicationScenarioDTO, MetalAnalysisDTO
from domain.agronomy.calculator import AgronomyCalculator
from domain.compliance.validator import ComplianceValidator
from domain.logistics.rules import LogisticsRules
from domain.exceptions import AgronomicException, ComplianceException, LogisticsException

def test_agronomy():
    print("\n--- Testing Agronomy ---")
    # Scenario: Anaerobic Digestion, Surface Application
    analysis = NutrientAnalysisDTO(
        nitrate_no3=100.0,   # mg/kg
        ammonium_nh4=2000.0, # mg/kg
        tkn=40000.0,         # mg/kg (4%)
        percent_solids=20.0
    )
    scenario = ApplicationScenarioDTO(crop_n_requirement=150.0, injection_method=False)
    
    # PAN Calculation
    # NO3 term: 100 * 0.002 = 0.2
    # NH4 term: 0.7 * (2000 * 0.002) = 0.7 * 4 = 2.8
    # Norg term: 0.2 * ((40000 - 2000) * 0.002) = 0.2 * (38000 * 0.002) = 0.2 * 76 = 15.2
    # Total PAN = 0.2 + 2.8 + 15.2 = 18.2 lbs/ton
    pan = AgronomyCalculator.calculate_pan(analysis, scenario, 'Anaerobic_Digestion')
    print(f"Calculated PAN: {pan:.2f} lbs/dry_ton (Expected ~18.2)")

    # Rate Calculation
    # Rate = 150 / 18.2 = 8.24 dry tons/acre
    rate = AgronomyCalculator.calculate_max_application_rate(pan, scenario.crop_n_requirement)
    print(f"Max Application Rate: {rate:.2f} dry tons/acre")
    
    # Wet Tons
    # Wet = 8.24 / 0.20 = 41.2
    wet_rate = AgronomyCalculator.convert_to_wet_tons(rate, analysis.percent_solids)
    print(f"Max Wet Rate: {wet_rate:.2f} wet tons/acre")

def test_compliance():
    print("\n--- Testing Compliance ---")
    # 1. Metals
    clean_metals = MetalAnalysisDTO(arsenic=10, cadmium=10, copper=100, lead=100, mercury=1, nickel=10, selenium=10, zinc=1000)
    try:
        ComplianceValidator.validate_heavy_metals(clean_metals)
        print("Clean metals: OK")
    except ComplianceException as e:
        print(f"Clean metals FAILED: {e}")

    dirty_metals = MetalAnalysisDTO(arsenic=80) # Limit is 75
    try:
        ComplianceValidator.validate_heavy_metals(dirty_metals)
        print("Dirty metals: OK (Unexpected)")
    except ComplianceException as e:
        print(f"Dirty metals CAUGHT: {e}")

    # 2. Class Restrictions
    try:
        ComplianceValidator.validate_class_restrictions('B', 'Public Park')
        print("Class B on Park: OK (Unexpected)")
    except ComplianceException as e:
        print(f"Class B on Park CAUGHT: {e}")

def test_logistics():
    print("\n--- Testing Logistics ---")
    # 1. Net Weight
    try:
        net = LogisticsRules.calculate_net_weight(30000, 12000)
        print(f"Net Weight: {net} (Expected 18000)")
    except LogisticsException as e:
        print(f"Net Weight Error: {e}")

    # 2. Capacity
    # Max 20000
    print(f"Status (18000/20000): {LogisticsRules.validate_vehicle_capacity(18000, 20000)}")
    print(f"Status (21000/20000): {LogisticsRules.validate_vehicle_capacity(21000, 20000)}") # Warning
    
    try:
        LogisticsRules.validate_vehicle_capacity(23000, 20000) # > 10% -> Block
        print("Critical Overweight: OK (Unexpected)")
    except LogisticsException as e:
        print(f"Critical Overweight CAUGHT: {e}")

if __name__ == "__main__":
    test_agronomy()
    test_compliance()
    test_logistics()

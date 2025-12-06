"""
Test Suite para Servicios de Dominio Financiero.

Valida los 4 servicios principales:
1. TariffAdjustmentService (Factor Polinómico)
2. TransportCostCalculator (Costos de Transporte)
3. ClientRevenueCalculator (Ingresos de Clientes)
4. FinancialReportingService (Reportes Masivos)

Arquitectura: Tests puros sin dependencias de BD (excepto el servicio #4).
"""

import unittest
from datetime import date, datetime
from typing import List

# Servicios bajo test
from domain.finance.services.tariff_adjustment_service import TariffAdjustmentService
from domain.finance.services.cost_calculator_service import TransportCostCalculator
from domain.finance.services.revenue_calculator_service import ClientRevenueCalculator

# Entidades y DTOs
from domain.finance.entities.finance_entities import (
    TariffRule,
    EconomicCycle,
    DistanceRoute,
    ClientTariff,
    TripCostResult,
    RevenueResult
)

# Excepciones
from domain.shared.exceptions import (
    InvalidFuelPriceError,
    InvalidRouteError,
    MissingTariffError
)


# Mock de Load para testing (evita importar logistics.entities.load)
class MockLoad:
    """Mock simplificado de Load para testing."""
    def __init__(
        self,
        id: int = 1,
        net_weight: float = 20.0,
        origin_facility_id: int = 1,
        destination_site_id: int = None,
        destination_treatment_plant_id: int = None,
        goes_to_treatment: bool = False
    ):
        self.id = id
        self.net_weight = net_weight
        self.origin_facility_id = origin_facility_id
        self.destination_site_id = destination_site_id
        self.destination_treatment_plant_id = destination_treatment_plant_id
        self.goes_to_treatment = goes_to_treatment


class TestTariffAdjustmentService(unittest.TestCase):
    """Test Suite para TariffAdjustmentService."""
    
    def test_fuel_price_increase(self):
        """
        Test: Precio de combustible SUBE.
        Escenario: Base 1000 CLP/L → Actual 1200 CLP/L (+20%)
        Resultado esperado: Factor = 1.2
        """
        factor = TariffAdjustmentService.calculate_fuel_factor(
            current_fuel_price=1200.0,
            base_fuel_price=1000.0
        )
        self.assertEqual(factor, 1.2)
    
    def test_fuel_price_decrease(self):
        """
        Test: Precio de combustible BAJA.
        Escenario: Base 1000 CLP/L → Actual 800 CLP/L (-20%)
        Resultado esperado: Factor = 0.8
        """
        factor = TariffAdjustmentService.calculate_fuel_factor(
            current_fuel_price=800.0,
            base_fuel_price=1000.0
        )
        self.assertEqual(factor, 0.8)
    
    def test_fuel_price_unchanged(self):
        """
        Test: Precio de combustible NO cambia.
        Escenario: Base 1000 CLP/L → Actual 1000 CLP/L (0%)
        Resultado esperado: Factor = 1.0
        """
        factor = TariffAdjustmentService.calculate_fuel_factor(
            current_fuel_price=1000.0,
            base_fuel_price=1000.0
        )
        self.assertEqual(factor, 1.0)
    
    def test_base_fuel_price_zero_raises_error(self):
        """
        Test: Validación de división por cero.
        Escenario: base_fuel_price = 0
        Resultado esperado: InvalidFuelPriceError
        """
        with self.assertRaises(InvalidFuelPriceError):
            TariffAdjustmentService.calculate_fuel_factor(
                current_fuel_price=1000.0,
                base_fuel_price=0.0
            )
    
    def test_base_fuel_price_negative_raises_error(self):
        """
        Test: Validación de precio base negativo.
        Escenario: base_fuel_price < 0
        Resultado esperado: InvalidFuelPriceError
        """
        with self.assertRaises(InvalidFuelPriceError):
            TariffAdjustmentService.calculate_fuel_factor(
                current_fuel_price=1000.0,
                base_fuel_price=-100.0
            )


class TestTransportCostCalculator(unittest.TestCase):
    """Test Suite para TransportCostCalculator."""
    
    def setUp(self):
        """Setup común para todos los tests."""
        self.calculator = TransportCostCalculator()
        
        # Tarifa base para Batea (15t mínimo, 0.027 UF/ton-km)
        self.tariff_batea = TariffRule(
            base_rate_uf=0.027,
            min_weight=15.0,
            vehicle_type='BATEA',
            base_fuel_price=1000.0
        )
        
        # Ciclo económico (combustible a 1200 CLP/L, incremento del 20%)
        self.cycle = EconomicCycle(
            uf_value=37000.0,
            fuel_price=1200.0,
            is_closed=True,
            start_date=date(2025, 10, 19),
            end_date=date(2025, 11, 18)
        )
    
    def test_simple_trip_above_minimum(self):
        """
        Test: Viaje simple con peso MAYOR al mínimo garantizado.
        Escenario: 1 carga de 20t, 50 km, tarifa 0.027 UF/ton-km
        Fórmula: 0.027 * 50 * 20 * 1.2 = 32.4 UF
        """
        load = MockLoad(net_weight=20.0, origin_facility_id=1, destination_site_id=10)
        route_map = [DistanceRoute(origin_id=1, destination_id=10, km=50.0)]
        
        result = self.calculator.calculate_trip_cost(
            loads=[load],
            route_map=route_map,
            tariff=self.tariff_batea,
            cycle=self.cycle
        )
        
        self.assertAlmostEqual(result.total_cost_uf, 32.4, places=2)
        self.assertEqual(result.adjustment_factor, 1.2)
        self.assertEqual(result.applied_weight, 20.0)
    
    def test_simple_trip_below_minimum(self):
        """
        Test: Viaje simple con peso MENOR al mínimo garantizado.
        Escenario: 1 carga de 10t (< 15t mínimo), 50 km
        Peso cobrado: 15t (mínimo garantizado)
        Fórmula: 0.027 * 50 * 15 * 1.2 = 24.3 UF
        """
        load = MockLoad(net_weight=10.0, origin_facility_id=1, destination_site_id=10)
        route_map = [DistanceRoute(origin_id=1, destination_id=10, km=50.0)]
        
        result = self.calculator.calculate_trip_cost(
            loads=[load],
            route_map=route_map,
            tariff=self.tariff_batea,
            cycle=self.cycle
        )
        
        self.assertAlmostEqual(result.total_cost_uf, 24.3, places=2)
        self.assertEqual(result.applied_weight, 15.0)  # Mínimo aplicado
    
    def test_consolidated_trip_two_loads(self):
        """
        Test: Viaje consolidado (enlace) con 2 cargas.
        Escenario:
        - Carga 1: Planta A (10t) → Planta B (30 km)
        - Carga 2: Planta B (8t) → Sitio C (40 km)
        
        Tramo 1 (A→B): max(10t, 15t mín) = 15t × 30 km = 450 ton-km
        Tramo 2 (B→C): max(18t, 15t mín) = 18t × 40 km = 720 ton-km
        Total: (450 + 720) × 0.027 × 1.2 = 37.908 UF
        """
        load1 = MockLoad(id=1, net_weight=10.0, origin_facility_id=1, destination_site_id=20)
        load2 = MockLoad(id=2, net_weight=8.0, origin_facility_id=2, destination_site_id=20)
        
        route_map = [
            DistanceRoute(origin_id=1, destination_id=2, km=30.0, is_segment_link=True),
            DistanceRoute(origin_id=2, destination_id=20, km=40.0, is_segment_link=False)
        ]
        
        result = self.calculator.calculate_trip_cost(
            loads=[load1, load2],
            route_map=route_map,
            tariff=self.tariff_batea,
            cycle=self.cycle
        )
        
        # Validar costo total (considerando mínimos garantizados en ambos tramos)
        # Tramo 1: 15t (mínimo) × 30km × 0.027 × 1.2 = 14.58 UF
        # Tramo 2: 18t × 40km × 0.027 × 1.2 = 23.328 UF
        # Total: 37.908 UF
        self.assertAlmostEqual(result.total_cost_uf, 37.908, places=2)
        
        # Validar desglose por tramos
        self.assertIn("Tramo 1", str(result.details))
        self.assertIn("Tramo 2", str(result.details))
    
    def test_missing_route_raises_error(self):
        """
        Test: Ruta no existe en la matriz de distancias.
        Escenario: Load requiere ruta 1→99, pero no está en route_map
        Resultado esperado: InvalidRouteError
        """
        load = MockLoad(origin_facility_id=1, destination_site_id=99)
        route_map = [DistanceRoute(origin_id=1, destination_id=10, km=50.0)]
        
        with self.assertRaises(InvalidRouteError):
            self.calculator.calculate_trip_cost(
                loads=[load],
                route_map=route_map,
                tariff=self.tariff_batea,
                cycle=self.cycle
            )


class TestClientRevenueCalculator(unittest.TestCase):
    """Test Suite para ClientRevenueCalculator."""
    
    def setUp(self):
        """Setup común para todos los tests."""
        self.calculator = ClientRevenueCalculator()
        
        # Tarifas de cliente (vigentes hoy)
        self.tariffs = [
            ClientTariff(
                client_id=1,
                concept='TRANSPORTE',
                rate_uf=0.5,
                min_weight=6.0,
                valid_from=date(2025, 1, 1),
                valid_to=None
            ),
            ClientTariff(
                client_id=1,
                concept='DISPOSICION',
                rate_uf=0.3,
                min_weight=6.0,
                valid_from=date(2025, 1, 1),
                valid_to=None
            ),
            ClientTariff(
                client_id=1,
                concept='TRATAMIENTO',
                rate_uf=0.2,
                min_weight=0.0,
                valid_from=date(2025, 1, 1),
                valid_to=None
            )
        ]
        
        self.uf_value = 37000.0
    
    def test_load_without_treatment(self):
        """
        Test: Carga SIN tratamiento.
        Escenario: 20t, no pasa por planta de tratamiento
        Conceptos: TRANSPORTE + DISPOSICION (NO TRATAMIENTO)
        Cálculo: (0.5 + 0.3) * 20 = 16.0 UF
        """
        load = MockLoad(net_weight=20.0, goes_to_treatment=False)
        
        result = self.calculator.calculate_load_revenue(
            load=load,
            tariffs=self.tariffs,
            uf_value=self.uf_value
        )
        
        self.assertAlmostEqual(result.total_uf, 16.0, places=2)
        self.assertAlmostEqual(result.total_clp, 592000.0, places=2)
        
        # Validar desglose
        self.assertEqual(result.details['TRANSPORTE'], 10.0)
        self.assertEqual(result.details['DISPOSICION'], 6.0)
        self.assertEqual(result.details['TRATAMIENTO'], 0.0)
    
    def test_load_with_treatment(self):
        """
        Test: Carga CON tratamiento.
        Escenario: 20t, pasa por planta de tratamiento
        Conceptos: TRANSPORTE + DISPOSICION + TRATAMIENTO
        Cálculo: (0.5 + 0.3 + 0.2) * 20 = 20.0 UF
        """
        load = MockLoad(net_weight=20.0, goes_to_treatment=True)
        
        result = self.calculator.calculate_load_revenue(
            load=load,
            tariffs=self.tariffs,
            uf_value=self.uf_value
        )
        
        self.assertAlmostEqual(result.total_uf, 20.0, places=2)
        self.assertAlmostEqual(result.total_clp, 740000.0, places=2)
        
        # Validar desglose
        self.assertEqual(result.details['TRANSPORTE'], 10.0)
        self.assertEqual(result.details['DISPOSICION'], 6.0)
        self.assertEqual(result.details['TRATAMIENTO'], 4.0)
    
    def test_minimum_weight_guarantee(self):
        """
        Test: Peso real MENOR al mínimo garantizado.
        Escenario: Carga de 4t (< 6t mínimo)
        Peso cobrado: 6t (mínimo garantizado)
        Cálculo: (0.5 + 0.3) * 6 = 4.8 UF
        """
        load = MockLoad(net_weight=4.0, goes_to_treatment=False)
        
        result = self.calculator.calculate_load_revenue(
            load=load,
            tariffs=self.tariffs,
            uf_value=self.uf_value
        )
        
        self.assertAlmostEqual(result.total_uf, 4.8, places=2)
        
        # Ambos conceptos deben cobrar el mínimo de 6t
        self.assertAlmostEqual(result.details['TRANSPORTE'], 3.0, places=5)  # 0.5 * 6
        self.assertAlmostEqual(result.details['DISPOSICION'], 1.8, places=5)  # 0.3 * 6
    
    def test_missing_transport_tariff_raises_error(self):
        """
        Test: Falta tarifa obligatoria (TRANSPORTE).
        Escenario: Tarifas no incluyen TRANSPORTE
        Resultado esperado: MissingTariffError
        """
        load = MockLoad(net_weight=20.0)
        
        # Tarifas sin TRANSPORTE
        tariffs_incomplete = [
            ClientTariff(
                client_id=1,
                concept='DISPOSICION',
                rate_uf=0.3,
                min_weight=6.0,
                valid_from=date(2025, 1, 1),
                valid_to=None
            )
        ]
        
        with self.assertRaises(MissingTariffError):
            self.calculator.calculate_load_revenue(
                load=load,
                tariffs=tariffs_incomplete,
                uf_value=self.uf_value
            )
    
    def test_tariff_validity_filtering(self):
        """
        Test: Filtrado de tarifas por vigencia.
        Escenario: Tarifa TRANSPORTE expiró el 31-Oct-2025
        Cálculo en Nov-2025 debe fallar (tarifa no vigente)
        """
        load = MockLoad(net_weight=20.0)
        
        # Tarifa expirada
        tariffs_expired = [
            ClientTariff(
                client_id=1,
                concept='TRANSPORTE',
                rate_uf=0.5,
                min_weight=6.0,
                valid_from=date(2025, 1, 1),
                valid_to=date(2025, 10, 31)  # Expiró
            ),
            ClientTariff(
                client_id=1,
                concept='DISPOSICION',
                rate_uf=0.3,
                min_weight=6.0,
                valid_from=date(2025, 1, 1),
                valid_to=None
            )
        ]
        
        # Cálculo en noviembre (después de expiración)
        calculation_date = date(2025, 11, 5)
        
        with self.assertRaises(MissingTariffError):
            self.calculator.calculate_load_revenue(
                load=load,
                tariffs=tariffs_expired,
                uf_value=self.uf_value,
                calculation_date=calculation_date
            )


class TestEntityValidations(unittest.TestCase):
    """Test Suite para validaciones de Entidades de Dominio."""
    
    def test_tariff_rule_invalid_base_rate(self):
        """Test: TariffRule con base_rate_uf negativa."""
        with self.assertRaises(ValueError):
            TariffRule(
                base_rate_uf=-0.027,
                min_weight=15.0,
                vehicle_type='BATEA',
                base_fuel_price=1000.0
            )
    
    def test_tariff_rule_invalid_vehicle_type(self):
        """Test: TariffRule con vehicle_type inválido."""
        with self.assertRaises(ValueError):
            TariffRule(
                base_rate_uf=0.027,
                min_weight=15.0,
                vehicle_type='CAMION_INVALIDO',
                base_fuel_price=1000.0
            )
    
    def test_economic_cycle_invalid_dates(self):
        """Test: EconomicCycle con end_date anterior a start_date."""
        with self.assertRaises(ValueError):
            EconomicCycle(
                uf_value=37000.0,
                fuel_price=1200.0,
                is_closed=True,
                start_date=date(2025, 11, 18),
                end_date=date(2025, 10, 19)  # Anterior a start_date
            )
    
    def test_distance_route_negative_km(self):
        """Test: DistanceRoute con km negativa."""
        with self.assertRaises(ValueError):
            DistanceRoute(
                origin_id=1,
                destination_id=10,
                km=-50.0
            )
    
    def test_client_tariff_invalid_concept(self):
        """Test: ClientTariff con concepto inválido."""
        with self.assertRaises(ValueError):
            ClientTariff(
                client_id=1,
                concept='CONCEPTO_INVALIDO',
                rate_uf=0.5,
                min_weight=6.0,
                valid_from=date(2025, 1, 1)
            )


# ==========================================
# Runner Principal
# ==========================================

if __name__ == '__main__':
    # Ejecutar todos los tests con output verbose
    unittest.main(verbosity=2)

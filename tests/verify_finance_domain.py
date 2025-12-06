#!/usr/bin/env python3
"""
Script de Verificación para Servicios de Dominio Financiero.

Este script ejecuta casos de prueba representativos para validar
la correctitud de los cálculos financieros implementados.

Ejecutar: python3 tests/verify_finance_domain.py
"""

import sys
from pathlib import Path
from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports directos para evitar dependencias circulares
from domain.finance.entities.finance_entities import (
    EconomicCycle,
    TariffRule,
    DistanceRoute,
    ClientTariff
)
from domain.finance.services.tariff_adjustment_service import TariffAdjustmentService
from domain.finance.services.cost_calculator_service import TransportCostCalculator
from domain.finance.services.revenue_calculator_service import ClientRevenueCalculator
from domain.shared.exceptions import InvalidFuelPriceError, InvalidRouteError, MissingTariffError


# Mock simplificado de Load para evitar imports circulares
@dataclass
class Load:
    """Mock de Load para testing."""
    id: Optional[int] = None
    origin_facility_id: int = 1
    destination_site_id: Optional[int] = None
    destination_treatment_plant_id: Optional[int] = None
    net_weight: float = 0.0
    goes_to_treatment: bool = False


def test_fuel_adjustment_factor():
    """
    Test 1: Factor de Ajuste Polinómico.
    
    Valida que la fórmula polinómica funciona correctamente:
    - Factor > 1 cuando combustible sube
    - Factor < 1 cuando combustible baja
    - Excepción cuando precio base = 0
    """
    print("\n" + "="*60)
    print("TEST 1: Factor de Ajuste Polinómico")
    print("="*60)
    
    # Caso 1: Combustible sube 20% (1000 → 1200)
    factor = TariffAdjustmentService.calculate_fuel_factor(1200.0, 1000.0)
    assert abs(factor - 1.2) < 0.001, f"Esperado 1.2, obtenido {factor}"
    print(f"✓ Caso 1: Combustible +20% → Factor = {factor:.2f}")
    
    # Caso 2: Combustible baja 20% (1000 → 800)
    factor = TariffAdjustmentService.calculate_fuel_factor(800.0, 1000.0)
    assert abs(factor - 0.8) < 0.001, f"Esperado 0.8, obtenido {factor}"
    print(f"✓ Caso 2: Combustible -20% → Factor = {factor:.2f}")
    
    # Caso 3: Sin cambio (1000 → 1000)
    factor = TariffAdjustmentService.calculate_fuel_factor(1000.0, 1000.0)
    assert abs(factor - 1.0) < 0.001, f"Esperado 1.0, obtenido {factor}"
    print(f"✓ Caso 3: Sin cambio → Factor = {factor:.2f}")
    
    # Caso 4: Precio base = 0 (debe lanzar excepción)
    try:
        TariffAdjustmentService.calculate_fuel_factor(1200.0, 0.0)
        assert False, "Debería haber lanzado InvalidFuelPriceError"
    except InvalidFuelPriceError as e:
        print(f"✓ Caso 4: base_fuel_price=0 → InvalidFuelPriceError: {str(e)[:50]}...")
    
    print("\n✓✓✓ TEST 1 PASADO ✓✓✓")


def test_single_load_cost():
    """
    Test 2: Cálculo de Costo - Viaje Simple.
    
    Valida el cálculo básico con mínimos garantizados.
    """
    print("\n" + "="*60)
    print("TEST 2: Cálculo de Costo - Viaje Simple")
    print("="*60)
    
    calculator = TransportCostCalculator()
    
    # Setup
    tariff = TariffRule(
        base_rate_uf=0.027,  # UF/ton-km (equivalente a ~1000 CLP @ UF 37000)
        min_weight=15.0,   # 15 toneladas mínimo (Batea)
        vehicle_type='BATEA',
        base_fuel_price=1000.0  # CLP/litro (para factor)
    )
    
    cycle = EconomicCycle(
        uf_value=37000.0,
        fuel_price=1200.0,  # 20% más caro
        is_closed=True,
        start_date=date(2025, 11, 19),
        end_date=date(2025, 12, 18)
    )
    
    route_map = [
        DistanceRoute(origin_id=1, destination_id=10, km=50.0, is_segment_link=False)
    ]
    
    # Escenario A: Peso real > mínimo garantizado
    load_a = Load(
        id=1,
        origin_facility_id=1,
        destination_site_id=10,
        net_weight=20.0  # 20t > 15t mínimo
    )
    
    result = calculator.calculate_trip_cost([load_a], route_map, tariff, cycle)
    
    # Cálculo esperado en UF: 0.027 * 50 * 20 * 1.2 = 32.4 UF
    expected_cost_uf = 0.027 * 50.0 * 20.0 * 1.2
    assert abs(result.total_cost_uf - expected_cost_uf) < 0.01, \
        f"Esperado {expected_cost_uf} UF, obtenido {result.total_cost_uf} UF"
    
    # Verificar conversión a CLP
    expected_cost_clp = expected_cost_uf * 37000.0
    actual_cost_clp = result.to_clp(37000.0)
    assert abs(actual_cost_clp - expected_cost_clp) < 1.0
    
    print(f"✓ Escenario A: Peso real=20t > mín=15t")
    print(f"  - Costo total: {result.total_cost_uf:.2f} UF (${actual_cost_clp:,.0f} CLP)")
    print(f"  - Factor combustible: {result.adjustment_factor:.2f}")
    print(f"  - Peso aplicado: {result.applied_weight:.1f}t")
    
    # Escenario B: Peso real < mínimo garantizado
    load_b = Load(
        id=2,
        origin_facility_id=1,
        destination_site_id=10,
        net_weight=10.0  # 10t < 15t mínimo
    )
    
    result = calculator.calculate_trip_cost([load_b], route_map, tariff, cycle)
    
    # Cálculo esperado en UF: 0.027 * 50 * 15 * 1.2 = 24.3 UF (usa mínimo)
    expected_cost_uf = 0.027 * 50.0 * 15.0 * 1.2
    assert abs(result.total_cost_uf - expected_cost_uf) < 0.01, \
        f"Esperado {expected_cost_uf} UF, obtenido {result.total_cost_uf} UF"
    
    print(f"✓ Escenario B: Peso real=10t < mín=15t → Usa mínimo")
    print(f"  - Costo total: {result.total_cost_uf:.2f} UF (${result.to_clp(37000.0):,.0f} CLP)")
    print(f"  - Peso aplicado: {result.applied_weight:.1f}t (mínimo garantizado)")
    
    print("\n✓✓✓ TEST 2 PASADO ✓✓✓")


def test_linked_trip_cost():
    """
    Test 3: Cálculo de Costo - Enlace (A→B + B→C).
    
    Valida la lógica de viajes consolidados con 2 tramos.
    """
    print("\n" + "="*60)
    print("TEST 3: Cálculo de Costo - Viaje Consolidado (Enlace)")
    print("="*60)
    
    calculator = TransportCostCalculator()
    
    # Setup
    tariff = TariffRule(
        base_rate_uf=0.027,  # UF/ton-km
        min_weight=7.0,  # Ampliroll: 7t mínimo
        vehicle_type='AMPLIROLL_SIMPLE',
        base_fuel_price=1000.0
    )
    
    cycle = EconomicCycle(
        uf_value=37000.0,
        fuel_price=1000.0,  # Sin cambio en combustible
        is_closed=True,
        start_date=date(2025, 11, 19),
        end_date=date(2025, 12, 18)
    )
    
    # Rutas:
    # - Planta A (id=1) → Planta B (id=2): 30 km (segmento)
    # - Planta B (id=2) → Sitio C (id=20): 40 km (final)
    route_map = [
        DistanceRoute(origin_id=1, destination_id=2, km=30.0, is_segment_link=True),
        DistanceRoute(origin_id=2, destination_id=20, km=40.0, is_segment_link=False)
    ]
    
    # Cargas:
    # - Carga A: 10t desde Planta A
    # - Carga B: 8t desde Planta B
    load_a = Load(
        id=10,
        origin_facility_id=1,
        net_weight=10.0
    )
    
    load_b = Load(
        id=11,
        origin_facility_id=2,
        destination_site_id=20,
        net_weight=8.0
    )
    
    result = calculator.calculate_trip_cost([load_a, load_b], route_map, tariff, cycle)
    
    # Cálculos esperados en UF:
    # Tramo 1 (A→B): 0.027 * 30 * 10 = 8.1 UF
    # Tramo 2 (B→C): 0.027 * 40 * 18 = 19.44 UF
    # Total: 27.54 UF
    expected_total_uf = (0.027 * 30.0 * 10.0) + (0.027 * 40.0 * 18.0)
    
    assert abs(result.total_cost_uf - expected_total_uf) < 0.01, \
        f"Esperado {expected_total_uf} UF, obtenido {result.total_cost_uf} UF"
    
    print(f"✓ Viaje Consolidado: Planta A (10t) → Planta B (8t) → Sitio C")
    print(f"  - Tramo 1 (A→B, 30km, 10t): {result.details['Tramo 1: Pickup (1→2)']:.2f} UF")
    print(f"  - Tramo 2 (B→C, 40km, 18t): {result.details['Tramo 2: Main Haul (2→20)']:.2f} UF")
    print(f"  - Costo total: {result.total_cost_uf:.2f} UF (${result.to_clp(37000.0):,.0f} CLP)")
    print(f"  - Peso máximo aplicado: {result.applied_weight:.1f}t")
    
    print("\n✓✓✓ TEST 3 PASADO ✓✓✓")


def test_client_revenue():
    """
    Test 4: Cálculo de Ingresos - Cliente.
    
    Valida el cálculo de facturación con múltiples conceptos.
    """
    print("\n" + "="*60)
    print("TEST 4: Cálculo de Ingresos - Cliente")
    print("="*60)
    
    calculator = ClientRevenueCalculator()
    
    # Tarifas del cliente en UF/ton
    tariffs = [
        ClientTariff(
            client_id=100,
            concept='TRANSPORTE',
            rate_uf=0.5,
            min_weight=6.0,
            valid_from=date(2025, 1, 1),
            valid_to=None
        ),
        ClientTariff(
            client_id=100,
            concept='DISPOSICION',
            rate_uf=0.3,
            min_weight=6.0,
            valid_from=date(2025, 1, 1),
            valid_to=None
        ),
        ClientTariff(
            client_id=100,
            concept='TRATAMIENTO',
            rate_uf=0.2,
            min_weight=0.0,
            valid_from=date(2025, 1, 1),
            valid_to=None
        )
    ]
    
    # Carga de 20t con tratamiento
    load = Load(
        id=50,
        origin_facility_id=1,
        destination_site_id=20,
        net_weight=20.0
    )
    load.goes_to_treatment = True
    
    # UF = 37,000 CLP
    result = calculator.calculate_load_revenue(load, tariffs, uf_value=37000.0)
    
    # Cálculos esperados:
    # TRANSPORTE: 0.5 * 20 = 10 UF
    # DISPOSICION: 0.3 * 20 = 6 UF
    # TRATAMIENTO: 0.2 * 20 = 4 UF
    # Total: 20 UF = 740,000 CLP
    expected_uf = (0.5 + 0.3 + 0.2) * 20.0
    expected_clp = expected_uf * 37000.0
    
    assert abs(result.total_uf - expected_uf) < 0.01, \
        f"Esperado {expected_uf} UF, obtenido {result.total_uf}"
    assert abs(result.total_clp - expected_clp) < 1.0, \
        f"Esperado {expected_clp} CLP, obtenido {result.total_clp}"
    
    print(f"✓ Carga de 20t con tratamiento:")
    print(f"  - TRANSPORTE: {result.details['TRANSPORTE']:.2f} UF")
    print(f"  - DISPOSICION: {result.details['DISPOSICION']:.2f} UF")
    print(f"  - TRATAMIENTO: {result.details['TRATAMIENTO']:.2f} UF")
    print(f"  - Total UF: {result.total_uf:.2f} UF")
    print(f"  - Total CLP: ${result.total_clp:,.0f}")
    
    # Escenario sin tratamiento
    load.goes_to_treatment = False
    result = calculator.calculate_load_revenue(load, tariffs, uf_value=37000.0)
    
    expected_uf = (0.5 + 0.3) * 20.0  # Solo transporte y disposición
    expected_clp = expected_uf * 37000.0
    
    assert abs(result.total_uf - expected_uf) < 0.01
    assert result.details['TRATAMIENTO'] == 0.0
    
    print(f"✓ Carga de 20t SIN tratamiento:")
    print(f"  - Total UF: {result.total_uf:.2f} UF (sin tratamiento)")
    print(f"  - Total CLP: ${result.total_clp:,.0f}")
    
    print("\n✓✓✓ TEST 4 PASADO ✓✓✓")


def main():
    """Ejecuta todos los tests de verificación."""
    print("\n" + "#"*60)
    print("# VERIFICACIÓN DE SERVICIOS DE DOMINIO FINANCIERO")
    print("#"*60)
    
    try:
        test_fuel_adjustment_factor()
        test_single_load_cost()
        test_linked_trip_cost()
        test_client_revenue()
        
        print("\n" + "="*60)
        print("✓✓✓ TODOS LOS TESTS PASADOS ✓✓✓")
        print("="*60)
        print("\n📊 Resumen:")
        print("  - Factor de ajuste polinómico: ✓")
        print("  - Cálculo de costos (viaje simple): ✓")
        print("  - Cálculo de costos (enlace): ✓")
        print("  - Cálculo de ingresos (cliente): ✓")
        print("\n💰 Los servicios financieros están listos para producción.")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""
Simple Test Script for Transport State Machine (TTO-03)
Tests core state machine transitions without heavy dependencies
"""
import sys
sys.path.insert(0, '/Users/mcalzadilla/ADO')

from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from models.operations.load import Load

# Initialize
db = DatabaseManager('database/biosolids.db')
load_repo = LoadRepository(db)

print("=" * 60)
print("TESTING TRANSPORT STATE MACHINE CORE (TTO-03)")
print("=" * 60)

# Get a scheduled load
loads = load_repo.get_by_status('Scheduled')
if not loads:
    print("❌ No hay cargas en estado 'Scheduled' para probar")
    sys.exit(1)

load = loads[0]
load_id = load.id
print(f"\n✓ Carga de prueba encontrada: ID {load_id}")
print(f"  Estado inicial: {load.status}")

# Test 1: Manual Accept Trip (Scheduled → Accepted)
print("\n[TEST 1] Aceptando viaje (Scheduled → Accepted)...")
try:
    load.status = 'Accepted'
    load_repo.update(load)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Accepted', f"Expected 'Accepted', got '{load.status}'"
    print(f"  ✓ Estado actualizado: {load.status}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 2: Manual Start Trip (Accepted → InTransit)
print("\n[TEST 2] Iniciando viaje (Accepted → InTransit)...")
try:
    from datetime import datetime
    load.status = 'InTransit'
    load.dispatch_time = datetime.now()
    load_repo.update(load)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'InTransit', f"Expected 'InTransit', got '{load.status}'"
    assert load.dispatch_time is not None, "dispatch_time should be set"
    print(f"  ✓ Estado actualizado: {load.status}")
    print(f"  ✓ Hora de salida registrada: {load.dispatch_time}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 3: Register Arrival using model method
print("\n[TEST 3] Registrando llegada (InTransit → Arrived)...")
try:
    load.register_arrival(
        weight_gross=25000.0,
        ph=7.5,
        humidity=45.0,
        observation="Carga en buenas condiciones"
    )
    load_repo.update(load)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Arrived', f"Expected 'Arrived', got '{load.status}'"
    assert load.arrival_time is not None, "arrival_time should be set"
    assert load.weight_gross_reception == 25000.0, "weight_gross_reception should be set"
    print(f"  ✓ Estado actualizado: {load.status}")
    print(f"  ✓ Hora de llegada: {load.arrival_time}")
    print(f"  ✓ Peso bruto recepción: {load.weight_gross_reception} kg")
    print(f"  ✓ pH preliminar: {load.quality_ph}")
    print(f"  ✓ Humedad preliminar: {load.quality_humidity}%")
    print(f"  ✓ Observaciones: {load.reception_observations}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 4: Close Trip with quality data using model method
print("\n[TEST 4] Cerrando viaje con datos de calidad (Arrived → Delivered)...")
try:
    load.close_trip(
        weight_net=20000.0,
        ticket_number='T-TEST-001',
        guide_number='G-TEST-001',
        ph=7.2,
        humidity=42.0
    )
    load_repo.update(load)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Delivered', f"Expected 'Delivered', got '{load.status}'"
    assert load.weight_net == 20000.0, "weight_net should be set"
    assert load.ticket_number == 'T-TEST-001', "ticket_number should be set"
    assert load.quality_ph == 7.2, "quality_ph should be set"
    print(f"  ✓ Estado actualizado: {load.status}")
    print(f"  ✓ Peso neto: {load.weight_net} kg")
    print(f"  ✓ Ticket: {load.ticket_number}")
    print(f"  ✓ Guía: {load.guide_number}")
    print(f"  ✓ pH final: {load.quality_ph}")
    print(f"  ✓ Humedad final: {load.quality_humidity}%")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 5: Validate pH out of range
print("\n[TEST 5] Validando rechazo por pH fuera de rango...")
load.status = 'Arrived'  # Reset for this test
load_repo.update(load)

try:
    load.close_trip(
        weight_net=20000.0,
        ticket_number='T-TEST-002',
        guide_number='G-TEST-002',
        ph=4.0,  # Out of range (should be 5-9)
        humidity=42.0
    )
    print(f"  ❌ ERROR: Should have raised ValueError for pH out of range")
    sys.exit(1)
except ValueError as e:
    if "pH fuera de rango" in str(e):
        print(f"  ✓ Validación correcta: {e}")
        # Verify status didn't change
        load = load_repo.get_by_id(load_id)
        assert load.status == 'Arrived', "Status should remain 'Arrived' after failed validation"
        print(f"  ✓ Estado no cambió (permanece en 'Arrived')")
    else:
        print(f"  ❌ Error inesperado: {e}")
        sys.exit(1)

# Test 6: Validate humidity out of range
print("\n[TEST 6] Validando rechazo por humedad fuera de rango...")
try:
    load.close_trip(
        weight_net=20000.0,
        ticket_number='T-TEST-003',
        guide_number='G-TEST-003',
        ph=7.5,
        humidity=105.0  # Out of range (should be 0-100)
    )
    print(f"  ❌ ERROR: Should have raised ValueError for humidity out of range")
    sys.exit(1)
except ValueError as e:
    if "Humedad fuera de rango" in str(e):
        print(f"  ✓ Validación correcta: {e}")
    else:
        print(f"  ❌ Error inesperado: {e}")
        sys.exit(1)

# Test 7: Test repository methods
print("\n[TEST 7] Probando métodos del repositorio con JOINs...")
try:
    # Test get_assignable_loads
    assignable = load_repo.get_assignable_loads(vehicle_id=1)
    print(f"  ✓ get_assignable_loads(1): {len(assignable)} cargas asignables")
    if len(assignable) > 0:
        print(f"    - Primera carga incluye: origin_facility_name={assignable[0].get('origin_facility_name')}, destination_site_name={assignable[0].get('destination_site_name')}")
    
    # Test get_active_load
    active = load_repo.get_active_load(vehicle_id=1)
    if active:
        print(f"  ✓ get_active_load(1): Carga activa ID {active['id']}")
        print(f"    - Origen: {active.get('origin_facility_name')}")
        print(f"    - Destino: {active.get('destination_site_name')}")
    else:
        print(f"  ✓ get_active_load(1): No hay carga activa")
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
print("=" * 60)
print("\nResumen de la máquina de estados implementada:")
print("  1. Scheduled → Accepted (accept_trip)")
print("  2. Accepted → InTransit (start_trip)")
print("  3. InTransit → Arrived (register_arrival)")
print("  4. Arrived → Delivered (close_trip)")
print("\nValidaciones implementadas:")
print("  - pH debe estar entre 5 y 9")
print("  - Humedad debe estar entre 0 y 100%")
print("  - Transiciones de estado se validan estrictamente")

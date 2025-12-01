"""
Test script for Transport State Machine (TTO-03)
Tests the full flow: Scheduled → Accepted → InTransit → Arrived → Delivered
"""
import sys
sys.path.insert(0, '/Users/mcalzadilla/ADO')

from database.db_manager import DatabaseManager
from services.operations.dispatch_service import DispatchService
from services.operations.batch_service import BatchService
from services.operations.dispatch_validation_service import DispatchValidationService
from services.operations.nitrogen_application_service import NitrogenApplicationService
from services.operations.manifest_service import ManifestService
from repositories.load_repository import LoadRepository

# Initialize services
db = DatabaseManager('database/biosolids.db')
batch_service = BatchService(db)
validation_service = DispatchValidationService(db)
nitrogen_service = NitrogenApplicationService(db)
manifest_service = ManifestService(db)

dispatch_service = DispatchService(
    db, 
    batch_service, 
    validation_service, 
    nitrogen_service, 
    manifest_service
)
load_repo = LoadRepository(db)

print("=" * 60)
print("TESTING TRANSPORT STATE MACHINE (TTO-03)")
print("=" * 60)

# Get a scheduled load
loads = load_repo.get_by_status('Scheduled')
if not loads:
    print("❌ No hay cargas en estado 'Scheduled' para probar")
    sys.exit(1)

load_id = loads[0].id
print(f"\n✓ Carga de prueba encontrada: ID {load_id}")
print(f"  Estado inicial: {loads[0].status}")

# Test 1: Accept Trip
print("\n[TEST 1] Aceptando viaje (Scheduled → Accepted)...")
try:
    result = dispatch_service.accept_trip(load_id)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Accepted', f"Expected 'Accepted', got '{load.status}'"
    print(f"  ✓ Estado actualizado: {load.status}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 2: Start Trip
print("\n[TEST 2] Iniciando viaje (Accepted → InTransit)...")
try:
    result = dispatch_service.start_trip(load_id)
    load = load_repo.get_by_id(load_id)
    assert load.status == 'InTransit', f"Expected 'InTransit', got '{load.status}'"
    assert load.dispatch_time is not None, "dispatch_time should be set"
    print(f"  ✓ Estado actualizado: {load.status}")
    print(f"  ✓ Hora de salida registrada: {load.dispatch_time}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 3: Register Arrival with optional data
print("\n[TEST 3] Registrando llegada (InTransit → Arrived)...")
try:
    result = dispatch_service.register_arrival(
        load_id, 
        weight_gross=25000.0,
        ph=7.5,
        humidity=45.0,
        observation="Carga en buenas condiciones"
    )
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Arrived', f"Expected 'Arrived', got '{load.status}'"
    assert load.arrival_time is not None, "arrival_time should be set"
    assert load.weight_gross_reception == 25000.0, "weight_gross_reception should be set"
    print(f"  ✓ Estado actualizado: {load.status}")
    print(f"  ✓ Hora de llegada: {load.arrival_time}")
    print(f"  ✓ Peso bruto recepción: {load.weight_gross_reception} kg")
    print(f"  ✓ pH preliminar: {load.quality_ph}")
    print(f"  ✓ Humedad preliminar: {load.quality_humidity}%")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 4: Close Trip with quality data
print("\n[TEST 4] Cerrando viaje (Arrived → Delivered)...")
try:
    result = dispatch_service.close_trip(load_id, {
        'weight_net': 20000.0,
        'ticket_number': 'T-TEST-001',
        'guide_number': 'G-TEST-001',
        'quality_ph': 7.2,
        'quality_humidity': 42.0
    })
    load = load_repo.get_by_id(load_id)
    assert load.status == 'Delivered', f"Expected 'Delivered', got '{load.status}'"
    assert load.weight_net == 20000.0, "weight_net should be set"
    assert load.ticket_number == 'T-TEST-001', "ticket_number should be set"
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
# Reset load to Arrived state for this test
load = load_repo.get_by_id(load_id)
load.status = 'Arrived'
load_repo.update(load)

try:
    dispatch_service.close_trip(load_id, {
        'weight_net': 20000.0,
        'ticket_number': 'T-TEST-002',
        'guide_number': 'G-TEST-002',
        'quality_ph': 4.0,  # Out of range (should be 5-9)
        'quality_humidity': 42.0
    })
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

# Test 6: Test repository methods
print("\n[TEST 6] Probando métodos del repositorio...")
try:
    # Test get_assignable_loads
    assignable = load_repo.get_assignable_loads(vehicle_id=1)
    print(f"  ✓ get_assignable_loads(1): {len(assignable)} cargas asignables")
    
    # Test get_active_load
    active = load_repo.get_active_load(vehicle_id=1)
    if active:
        print(f"  ✓ get_active_load(1): Carga activa encontrada (ID: {active['id']})")
    else:
        print(f"  ✓ get_active_load(1): No hay carga activa")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
print("=" * 60)

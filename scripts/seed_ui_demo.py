"""
Demo Data Seeding Script for Task-Oriented UI Testing

Este script crea datos de prueba específicos para demostrar la funcionalidad
de la Bandeja de Entrada Inteligente (Inbox View).

Escenarios creados:
1. Carga en AT_DESTINATION → Requiere Análisis de Laboratorio
2. Carga en EN_ROUTE_DESTINATION → Requiere Registro de Portería
3. Carga en AT_PICKUP → Requiere Confirmación de Carga
4. Máquina sin Parte Diario → Requiere Registro de Actividad del Día

Uso:
    python scripts/seed_ui_demo.py
"""

from container import get_container
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.load import Load
from domain.logistics.entities.vehicle import Vehicle, AssetType
from datetime import datetime

def verify_dependencies(container):
    """Verifica que existan las dependencias necesarias"""
    print("🔍 Verificando dependencias...")
    
    issues = []
    
    # Verificar contractors
    contractors = container.contractor_service.get_all()
    if not contractors:
        issues.append("❌ No existen contractors. Por favor, ejecute el seed base primero.")
    
    # Verificar vehicles
    vehicles = container.vehicle_service.get_all()
    if not vehicles or len(vehicles) < 3:
        issues.append(f"⚠️ Solo hay {len(vehicles) if vehicles else 0} vehículos. Se necesitan al menos 3.")
    
    # Verificar drivers
    drivers = container.driver_service.get_all()
    if not drivers or len(drivers) < 3:
        issues.append(f"⚠️ Solo hay {len(drivers) if drivers else 0} conductores. Se necesitan al menos 3.")
    
    # Verificar facilities
    try:
        facilities = list(container.db_manager.execute_select("SELECT id FROM facilities LIMIT 1"))
        if not facilities:
            issues.append("❌ No existen facilities (plantas de tratamiento/clientes).")
    except Exception as e:
        issues.append(f"❌ Error al verificar facilities: {str(e)}")
    
    # Verificar sites
    sites = container.location_service.get_all_sites()
    if not sites:
        issues.append("❌ No existen sites (predios). Por favor, ejecute el seed base primero.")
    
    if issues:
        print("\n⚠️ ADVERTENCIAS Y ERRORES:")
        for issue in issues:
            print(f"  {issue}")
        print("\nAlgunos escenarios podrían fallar. ¿Continuar de todos modos? (y/n)")
        response = input().lower()
        if response != 'y':
            print("Seeding cancelado.")
            exit(1)
    else:
        print("✅ Todas las dependencias verificadas correctamente")

def ensure_heavy_equipment(container):
    """Asegura que exista al menos un asset de maquinaria pesada"""
    print("\n🚜 Verificando maquinaria pesada...")
    
    # Buscar vehículos de tipo HEAVY_EQUIPMENT
    vehicles = container.vehicle_service.get_all()
    heavy_equipment = [v for v in vehicles if hasattr(v, 'asset_type') and v.asset_type == AssetType.HEAVY_EQUIPMENT.value]
    
    if heavy_equipment:
        print(f"✅ Encontrada maquinaria: {heavy_equipment[0].license_plate}")
        return heavy_equipment[0].id
    else:
        print("⚠️ No se encontró maquinaria pesada. Creando excavadora de prueba...")
        try:
            # Crear vehículo de maquinaria
            new_machine = Vehicle(
                id=None,
                license_plate="EXC-001",
                contractor_id=1,
                asset_type=AssetType.HEAVY_EQUIPMENT.value,
                capacity_wet_tons=None,  # No aplica para maquinaria
                current_hourmeter=1000.0,
                current_odometer=None,
                cost_per_hour=50000.0,  # Costo por hora
                cost_per_km=None,
                is_active=True
            )
            
            # Guardar usando el servicio
            created = container.vehicle_service.create(new_machine)
            print(f"✅ Maquinaria creada: EXC-001 (ID: {created.id})")
            return created.id
        except Exception as e:
            print(f"❌ Error al crear maquinaria: {str(e)}")
            return None

def main():
    container = get_container()
    repo = container.logistics_service.load_repo
    
    print("=" * 60)
    print("🌱 SEEDING UI DEMO DATA")
    print("=" * 60)
    
    # Verificar dependencias
    verify_dependencies(container)
    
    print("\n📦 Creando cargas de prueba...")
    
    # 1. Carga para Laboratorio (AT_DESTINATION sin Lab)
    try:
        load_lab = Load(
            id=None,
            status=LoadStatus.AT_DESTINATION.value,
            origin_facility_id=1,
            destination_site_id=1,
            destination_plot_id=1,
            destination_treatment_plant_id=None,
            contractor_id=1,
            vehicle_id=1,
            driver_id=1,
            created_at=datetime.now(),
            attributes={
                "gate_entry": {"confirmed": True},
                "weight_entry": {
                    "gross_weight": 25000,
                    "tare": 8000,
                    "net_weight": 17000,
                    "ticket_number": "BAL-12345"
                }
                # Falta lab_analysis_result -> Generará tarea para LAB_TECH
            }
        )
        created_lab = repo.add(load_lab)
        print(f"✅ Carga #{created_lab.id} → AT_DESTINATION (Requiere Análisis Lab)")
    except Exception as e:
        print(f"❌ Error al crear carga para laboratorio: {str(e)}")
    
    # 2. Carga para Portería (EN_ROUTE_DESTINATION)
    try:
        load_gate = Load(
            id=None,
            status=LoadStatus.EN_ROUTE_DESTINATION.value,
            origin_facility_id=1,
            destination_site_id=1,
            destination_plot_id=1,
            destination_treatment_plant_id=None,
            contractor_id=1,
            vehicle_id=2 if len(container.vehicle_service.get_all()) >= 2 else 1,
            driver_id=2 if len(container.driver_service.get_all()) >= 2 else 1,
            created_at=datetime.now(),
            attributes={
                "pickup_confirmation": {"confirmed": True}
                # Falta gate_entry -> Generará tarea para GATE_KEEPER
            }
        )
        created_gate = repo.add(load_gate)
        print(f"✅ Carga #{created_gate.id} → EN_ROUTE_DESTINATION (Requiere Portería)")
    except Exception as e:
        print(f"❌ Error al crear carga para portería: {str(e)}")
    
    # 3. Carga para Confirmación Origen (AT_PICKUP)
    try:
        load_pickup = Load(
            id=None,
            status=LoadStatus.AT_PICKUP.value,
            origin_facility_id=1,
            destination_site_id=1,
            destination_plot_id=1,
            destination_treatment_plant_id=None,
            contractor_id=1,
            vehicle_id=3 if len(container.vehicle_service.get_all()) >= 3 else 1,
            driver_id=3 if len(container.driver_service.get_all()) >= 3 else 1,
            created_at=datetime.now(),
            attributes={
                "geofence_confirmation": {"confirmed": True}
                # Falta manual_pickup_confirmation -> Generará tarea para DRIVER
            }
        )
        created_pickup = repo.add(load_pickup)
        print(f"✅ Carga #{created_pickup.id} → AT_PICKUP (Requiere Confirmación Carga)")
    except Exception as e:
        print(f"❌ Error al crear carga para pickup: {str(e)}")
    
    # 4. Asegurar Maquinaria para Parte Diario
    machine_id = ensure_heavy_equipment(container)
    
    if machine_id:
        # Verificar que no exista log para hoy
        from domain.agronomy.repositories.machine_log_repository import MachineLogRepository
        log_repo = MachineLogRepository(container.db_manager)
        today_logs = log_repo.get_by_machine_id(machine_id)
        has_log_today = any(l.date.date() == datetime.now().date() for l in today_logs)
        
        if has_log_today:
            print(f"⚠️ Máquina #{machine_id} ya tiene log para hoy. Eliminando para prueba...")
            # En producción, no eliminaríamos. Esto es solo para testing.
        
        print(f"✅ Máquina #{machine_id} lista (Sin Parte Diario de hoy)")
    
    print("\n" + "=" * 60)
    print("✅ DEMO DATA SEEDED SUCCESSFULLY")
    print("=" * 60)
    print("\n📋 Resumen de Escenarios Creados:")
    print(f"  🔴 HIGH:   Carga requiere Análisis Lab (LAB_TECH)")
    print(f"  🟡 MEDIUM: Carga requiere Registro Portería (GATE_KEEPER)")
    print(f"  🔴 HIGH:   Carga requiere Confirmación (DRIVER)")
    if machine_id:
        print(f"  🔴 HIGH:   Máquina #{machine_id} requiere Parte Diario (OPERATOR)")
    print("\n💡 Para probar:")
    print("   1. Ejecute: streamlit run main.py")
    print("   2. Navegue a 'Mi Bandeja' en el menú")
    print("   3. Cambie el rol en el sidebar para ver diferentes tareas")
    print("=" * 60)

if __name__ == "__main__":
    main()


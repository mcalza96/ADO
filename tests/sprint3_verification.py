import sys
import os
import json
from datetime import date, datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from services.compliance.compliance_service import ComplianceService
from services.operations.dispatch_service import DispatchService
from services.operations.batch_service import BatchService
from repositories.site_repository import SiteRepository
from repositories.load_repository import LoadRepository
from repositories.batch_repository import BatchRepository
from repositories.application_repository import ApplicationRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.facility_repository import FacilityRepository
from models.masters.location import Site, Plot, Facility
from models.masters.transport import Vehicle
from domain.exceptions import ComplianceViolationError

def run_verification():
    print("🚀 Iniciando Verificación Sprint 3: Compliance Agronómico\n")
    
    db = DatabaseManager("database/biosolids.db")
    
    # Initialize Services & Repos
    batch_service = BatchService(db)
    dispatch_service = DispatchService(db, batch_service)
    compliance_service = dispatch_service.compliance_service
    site_repo = SiteRepository(db)
    batch_repo = BatchRepository(db)
    vehicle_repo = VehicleRepository(db)
    facility_repo = FacilityRepository(db)
    
    # --- SETUP DATA ---
    print("🛠️  Configurando Datos de Prueba...")
    
    # 1. Create Facility
    facility = Facility(id=None, client_id=1, name="Planta Test", address="Calle Test 123")
    facility = facility_repo.add(facility)
    
    # 2. Create Site & Plot
    site = Site(id=None, name="Campo Test Compliance", region="RM")
    site = site_repo.add(site)
    
    plot = Plot(
        id=None, 
        site_id=site.id, 
        name="Plot A", 
        area_hectares=10.0, 
        crop_type="Corn", # Limit ~200 kg/ha -> Total 2000 kg
        nitrogen_limit_kg_per_ha=200.0
    )
    # We need to insert plot manually as site_repo might not have add_plot method exposed yet or it's internal
    # Let's check if we can add it via repo or direct SQL. 
    # SiteRepository usually manages sites. Let's use SQL for speed and certainty.
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO plots (site_id, name, area_hectares, crop_type, nitrogen_limit_kg_per_ha, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (site.id, plot.name, plot.area_hectares, plot.crop_type, plot.nitrogen_limit_kg_per_ha)
        )
        plot_id = cursor.lastrowid
        
    # 3. Create Vehicle
    vehicle = Vehicle(id=None, contractor_id=1, license_plate=f"TST-{datetime.now().strftime('%M%S')}", max_capacity=30000, tare_weight=12000, type="Batea")
    vehicle = vehicle_repo.add(vehicle)
    
    # --- TEST 1: CÁLCULO PAN ---
    print("\n🧪 Test 1: Verificación Cálculo PAN")
    # Batch with known values
    # NO3=100, NH4=200, TKN=500, Solids=20%
    # PAN = (100*0.002) + 0.5*(200*0.002) + 0.2*((500-200)*0.002)
    # PAN = 0.2 + 0.2 + 0.12 = 0.52 lbs/ton -> 0.26 kg/ton
    
    batch_pan = batch_service.create_daily_batch(
        facility_id=facility.id,
        batch_code=f"PAN-TEST-{datetime.now().strftime('%H%M%S')}",
        production_date=date.today(),
        initial_tonnage=100000,
        class_type="B",
        sludge_type="Anaerobic_Digestion"
    )
    
    # Update lab results manually
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE batches 
            SET nitrate_no3=100, ammonium_nh4=200, tkn=500, percent_solids=20 
            WHERE id=?
            """, 
            (batch_pan.id,)
        )
        
    agronomics = compliance_service.calculate_load_agronomics(batch_pan.id, 1000) # 1 ton wet
    print(f"   PAN Calculado: {agronomics['pan_kg_per_ton']:.4f} kg/ton (Esperado: ~0.26)")
    if 0.25 <= agronomics['pan_kg_per_ton'] <= 0.27:
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # --- TEST 2: BLOQUEO POR METALES ---
    print("\n🧪 Test 2: Bloqueo por Metales Pesados")
    batch_toxic = batch_service.create_daily_batch(
        facility_id=facility.id,
        batch_code=f"TOXIC-{datetime.now().strftime('%H%M%S')}",
        production_date=date.today(),
        initial_tonnage=50000,
        class_type="B"
    )
    
    # Set Arsenic to 100 (Limit 75)
    metals = json.dumps({'arsenic': 100.0, 'cadmium': 1.0})
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE batches SET heavy_metals_json=?, nitrate_no3=100, ammonium_nh4=100, tkn=500 WHERE id=?", 
            (metals, batch_toxic.id)
        )
        
    try:
        dispatch_service.dispatch_truck(
            batch_id=batch_toxic.id,
            driver_id=1,
            vehicle_id=vehicle.id,
            destination_site_id=site.id,
            origin_facility_id=facility.id,
            weight_net=10000
        )
        print("   ❌ FAILED: Should have blocked toxic batch")
    except ValueError as e:
        if "OPERACIÓN BLOQUEADA" in str(e) and "Arsenic" in str(e):
            print(f"   ✅ PASSED: Bloqueado correctamente - {str(e)}")
        else:
            print(f"   ❌ FAILED: Wrong error message - {str(e)}")

    # --- TEST 3: BLOQUEO POR EXCESO DE NITROGENO ---
    print("\n🧪 Test 3: Bloqueo por Exceso de Nitrógeno")
    # Site Limit: 200 kg/ha * 10 ha = 2000 kg Total
    # Batch PAN: ~0.26 kg/ton
    # To exceed 2000 kg, we need > 7692 tons. That's too much for a truck.
    # Let's lower the limit or increase PAN.
    # Let's set Site Limit to very low: 1 kg total.
    
    # Update plot limit
    with db as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE plots SET nitrogen_limit_kg_per_ha=0.1 WHERE id=?", (plot_id,))
        # Limit = 0.1 * 10 = 1 kg
        
    try:
        dispatch_service.dispatch_truck(
            batch_id=batch_pan.id, # PAN ~0.26 kg/ton
            driver_id=1,
            vehicle_id=vehicle.id,
            destination_site_id=site.id,
            origin_facility_id=facility.id,
            weight_net=20000 # 20 tons -> ~5.2 kg N > 1 kg Limit
        )
        print("   ❌ FAILED: Should have blocked due to N excess")
    except ValueError as e:
        if "OPERACIÓN BLOQUEADA" in str(e) and "Nitrogen Excess" in str(e):
            print(f"   ✅ PASSED: Bloqueado correctamente - {str(e)}")
        else:
            print(f"   ❌ FAILED: Wrong error message - {str(e)}")

    # --- TEST 4: DESPACHO EXITOSO Y REGISTRO ---
    print("\n🧪 Test 4: Despacho Exitoso y PDF")
    # Restore limit
    with db as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE plots SET nitrogen_limit_kg_per_ha=200.0 WHERE id=?", (plot_id,))
        
    try:
        result = dispatch_service.dispatch_truck(
            batch_id=batch_pan.id,
            driver_id=1,
            vehicle_id=vehicle.id,
            destination_site_id=site.id,
            origin_facility_id=facility.id,
            weight_net=10000 # 10 tons -> ~2.6 kg N (OK)
        )
        print(f"   ✅ PASSED: Despacho creado ID {result['load_id']}")
        
        # Verify PDF exists
        if result['pdf_path'] and os.path.exists(result['pdf_path']):
            print(f"   ✅ PASSED: PDF generado en {result['pdf_path']}")
        else:
            print("   ❌ FAILED: PDF not found")
            
        # Verify Application Record
        with db as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nitrogen_applications WHERE load_id=?", (result['load_id'],))
            app = cursor.fetchone()
            if app:
                print(f"   ✅ PASSED: Registro de aplicación creado ({app['nitrogen_applied_kg']:.2f} kg N)")
            else:
                print("   ❌ FAILED: No application record found")
                
    except Exception as e:
        print(f"   ❌ FAILED: Exception - {str(e)}")

if __name__ == "__main__":
    run_verification()

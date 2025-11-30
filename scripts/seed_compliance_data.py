import sys
import os
import json
from datetime import date, datetime
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from services.operations.batch_service import BatchService
from repositories.site_repository import SiteRepository
from repositories.facility_repository import FacilityRepository
from models.masters.location import Site, Plot, Facility

def seed_data():
    print("🌱 Sembrando datos de Compliance...")
    db = DatabaseManager("database/biosolids.db")
    
    batch_service = BatchService(db)
    site_repo = SiteRepository(db)
    facility_repo = FacilityRepository(db)
    
    # 1. Create Facility if needed
    facilities = facility_repo.get_all()
    if not facilities:
        facility = Facility(id=None, client_id=1, name="Planta Principal", address="Camino Real 100")
        facility = facility_repo.add(facility)
        facility_id = facility.id
    else:
        facility_id = facilities[0].id
        
    # 2. Create Site with Plot
    site = Site(id=None, name=f"Fundo Los Olivos {random.randint(1,99)}", region="RM")
    site = site_repo.add(site)
    
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO plots (site_id, name, area_hectares, crop_type, nitrogen_limit_kg_per_ha, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (site.id, "Sector Norte", 50.0, "Corn", 200.0)
        )
    print(f"✅ Sitio creado: {site.name} (Límite N: 200 kg/ha)")
    
    # 3. Create Valid Batch (High Quality)
    batch_good = batch_service.create_daily_batch(
        facility_id=facility_id,
        batch_code=f"LOTE-OK-{datetime.now().strftime('%H%M')}",
        production_date=date.today(),
        initial_tonnage=50000,
        class_type="A",
        sludge_type="Anaerobic_Digestion"
    )
    
    # Update lab results
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE batches 
            SET nitrate_no3=50, ammonium_nh4=100, tkn=300, percent_solids=25 
            WHERE id=?
            """, 
            (batch_good.id,)
        )
    print(f"✅ Lote creado: {batch_good.batch_code} (Clase A, PAN bajo)")
    
    # 4. Create Toxic Batch (High Metals)
    batch_toxic = batch_service.create_daily_batch(
        facility_id=facility_id,
        batch_code=f"LOTE-TOXIC-{datetime.now().strftime('%H%M')}",
        production_date=date.today(),
        initial_tonnage=20000,
        class_type="B",
        sludge_type="Anaerobic_Digestion"
    )
    
    metals = json.dumps({'arsenic': 80.0, 'cadmium': 5.0}) # Arsenic > 75
    with db as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE batches SET heavy_metals_json=?, nitrate_no3=100, ammonium_nh4=200, tkn=500, percent_solids=20 WHERE id=?", 
            (metals, batch_toxic.id)
        )
    print(f"✅ Lote creado: {batch_toxic.batch_code} (Clase B, Arsénico Alto)")
    
    print("\n✨ Datos sembrados exitosamente. Ahora puedes probar en la UI.")

if __name__ == "__main__":
    seed_data()

from database.db_manager import DatabaseManager
from domain.shared.entities.client import Client
from domain.processing.entities.facility import Facility
from domain.logistics.entities.contractor import Contractor
from domain.logistics.entities.vehicle import Vehicle, AssetType
from domain.logistics.entities.driver import Driver
from database.repository import BaseRepository
from scripts.reset_db import reset_db
from domain.shared.entities.location import Site, Plot

import os
import time

def seed_base_data():
    if os.path.exists("ado_system.db"):
        try:
            os.remove("ado_system.db")
            print("🔥 Force deleted ado_system.db")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Could not delete DB: {e}")
            
    reset_db()
    print("🌱 Seeding Base Master Data...")
    db = DatabaseManager()
    
    # Check if client already exists
    with db as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM clients")
        count = cursor.fetchone()[0]
        print(f"DEBUG: Client count before seeding: {count}")
    
    # Repositories
    client_repo = BaseRepository(db, Client, "clients")
    facility_repo = BaseRepository(db, Facility, "facilities")
    contractor_repo = BaseRepository(db, Contractor, "contractors")
    vehicle_repo = BaseRepository(db, Vehicle, "vehicles")
    driver_repo = BaseRepository(db, Driver, "drivers")
    
    # 1. Client & Facility
    client = Client(id=None, name="Aguas Andinas", rut="99.999.999-9")
    client = client_repo.add(client)
    print(f"✅ Client: {client.name}")
    
    facility = Facility(id=None, client_id=client.id, name="La Farfana", address="Ruta 78 km 15")
    facility = facility_repo.add(facility)
    print(f"✅ Facility: {facility.name}")
    
    # 2. Contractor
    contractor = Contractor(id=None, name="Transportes Logística Total", rut="77.777.777-7")
    contractor = contractor_repo.add(contractor)
    print(f"✅ Contractor: {contractor.name}")
    
    # 3. Vehicles
    # Truck 1
    v1 = Vehicle(
        id=None, contractor_id=contractor.id, license_plate="ABCD-10", 
        brand="Volvo", model="FH16", capacity_wet_tons=30.0, tare_weight=12000,
        asset_type=AssetType.ROAD_VEHICLE.value
    )
    v1 = vehicle_repo.add(v1)
    
    # Truck 2
    v2 = Vehicle(
        id=None, contractor_id=contractor.id, license_plate="WXYZ-99", 
        brand="Scania", model="R500", capacity_wet_tons=30.0, tare_weight=12500,
        asset_type=AssetType.ROAD_VEHICLE.value
    )
    v2 = vehicle_repo.add(v2)
    
    # Truck 3
    v3 = Vehicle(
        id=None, contractor_id=contractor.id, license_plate="TRUCK-03", 
        brand="Mercedes", model="Actros", capacity_wet_tons=30.0, tare_weight=12200,
        asset_type=AssetType.ROAD_VEHICLE.value
    )
    v3 = vehicle_repo.add(v3)
    
    # Heavy Machinery (for Maintenance/Log tests)
    m1 = Vehicle(
        id=None, contractor_id=contractor.id, license_plate="MAQ-001",
        brand="Caterpillar", model="D8T", capacity_wet_tons=0, tare_weight=35000,
        asset_type=AssetType.HEAVY_EQUIPMENT.value,
        current_hourmeter=1000.0
    )
    m1 = vehicle_repo.add(m1)
    
    print(f"✅ Vehicles Created: {v1.license_plate}, {v2.license_plate}, {v3.license_plate}, {m1.license_plate}")
    
    # 4. Drivers
    d1 = Driver(id=None, contractor_id=contractor.id, name="Juan Perez", rut="11.111.111-1")
    d1 = driver_repo.add(d1)
    
    d2 = Driver(id=None, contractor_id=contractor.id, name="Pedro Soto", rut="22.222.222-2")
    d2 = driver_repo.add(d2)
    
    d3 = Driver(id=None, contractor_id=contractor.id, name="Diego Diaz", rut="33.333.333-3")
    d3 = driver_repo.add(d3)
    
    print(f"✅ Drivers Created: {d1.name}, {d2.name}, {d3.name}")

    # 5. Site & Plot (Destination)
    
    site_repo = BaseRepository(db, Site, "sites")
    plot_repo = BaseRepository(db, Plot, "plots")
    
    site = Site(id=None, name="Fundo El Sauce", region="RM")
    site = site_repo.add(site)
    print(f"✅ Site Created: {site.name} (ID: {site.id})")
    
    plot = Plot(id=None, site_id=site.id, name="Sector Norte", area_hectares=50.0)
    plot = plot_repo.add(plot)
    print(f"✅ Plot Created: {plot.name} (ID: {plot.id})")

if __name__ == "__main__":
    seed_base_data()

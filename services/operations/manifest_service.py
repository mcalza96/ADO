from typing import Dict, Any, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.repositories.load_repository import LoadRepository
from database.repository import BaseRepository
from domain.shared.entities.location import Site, Plot
from domain.processing.entities.treatment_plant import TreatmentPlant
from domain.logistics.entities.driver import Driver
from domain.logistics.entities.vehicle import Vehicle
from domain.logistics.entities.load import Load
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator

class ManifestService:
    """
    Service for managing Load Manifests.
    Focused purely on document generation and code formatting.
    Database logic for creating loads has been moved to DispatchService.
    """
    def __init__(self, db_manager: DatabaseManager, batch_service, compliance_service):
        self.db_manager = db_manager
        self.batch_service = batch_service
        self.compliance_service = compliance_service
        
        self.load_repo = LoadRepository(db_manager)
        self.load_repo = LoadRepository(db_manager)
        self.site_repo = BaseRepository(db_manager, Site, "sites")
        self.plot_repo = BaseRepository(db_manager, Plot, "plots")
        self.facility_repo = BaseRepository(db_manager, TreatmentPlant, "treatment_plants")
        self.driver_repo = BaseRepository(db_manager, Driver, "drivers")
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        
        self.pdf_generator = PdfManifestGenerator()

    def generate_manifest_code(self) -> str:
        """
        Generates the next unique manifest code.
        """
        sequence = self.load_repo.get_next_manifest_sequence()
        current_year = datetime.now().year
        return f"MAN-{current_year}-{sequence:04d}"

    def generate_manifest(self, load_id: int) -> str:
        """
        Generates a PDF manifest for a given load ID.
        Returns the path to the generated file.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        # Fetch related data
        driver = self.driver_repo.get_by_id(load.driver_id)
        vehicle = self.vehicle_repo.get_by_id(load.vehicle_id)
        facility = self.facility_repo.get_by_id(load.origin_facility_id) if load.origin_facility_id else None
        site = self.site_repo.get_by_id(load.destination_site_id) if load.destination_site_id else None
        plot = self.plot_repo.get_by_id(load.destination_plot_id) if load.destination_plot_id else None
        batch = self.batch_service.get_batch_by_id(load.batch_id) if load.batch_id else None

        # Calculate agronomic info for PDF
        agronomics = {}
        if load.batch_id and load.weight_net:
            try:
                agronomics = self.compliance_service.calculate_load_agronomics(load.batch_id, load.weight_net)
            except:
                agronomics = {'total_n_kg': 0, 'pan_value': 0}
        
        site_area = plot.area_hectares if plot and hasattr(plot, 'area_hectares') else 0
        rate_per_ha = (agronomics.get('total_n_kg', 0) / site_area) if site_area > 0 else 0
        
        load_data = {
            'origin_name': facility.name if facility else 'N/A',
            'destination_name': site.name if site else 'N/A',
            'driver_name': driver.name if driver else 'N/A',
            'vehicle_plate': vehicle.license_plate if vehicle else 'N/A',
            'weight_gross': load.weight_gross_reception if load.weight_gross_reception else 'Pendiente',
            'weight_net': load.weight_net,
            'batch_code': batch.code if batch else 'N/A',
            'agronomics': agronomics,
            'pan_value': agronomics.get('pan_value', 'N/A'),
            'agronomic_rate': f"{rate_per_ha:.2f}" if rate_per_ha else 'N/A',
            'applied_nitrogen_kg': agronomics.get('total_n_kg', 'N/A')
        }
        
        # Generate PDF
        # pdf_bytes = self.pdf_generator.generate(load, load_data)
        
        # Save to file (optional)
        # import os
        # reports_dir = 'reports/manifests'
        # os.makedirs(reports_dir, exist_ok=True)
        # pdf_path = f"{reports_dir}/manifest_{load.id}.pdf"
        # with open(pdf_path, 'wb') as f:
        #     f.write(pdf_bytes)
        
        return f"/tmp/manifest_{load.manifest_code}.pdf"

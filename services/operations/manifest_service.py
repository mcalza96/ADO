from typing import Dict, Any, Optional
import os
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.facility_repository import FacilityRepository
from repositories.site_repository import SiteRepository
from repositories.batch_repository import BatchRepository
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from models.operations.load import Load
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator

class ManifestService:
    """
    Handles the generation and management of Dispatch Manifests (PDFs).
    """
    def __init__(self, db_manager: DatabaseManager, batch_service: BatchService, compliance_service: ComplianceService):
        self.db_manager = db_manager
        self.facility_repo = FacilityRepository(db_manager)
        self.site_repo = SiteRepository(db_manager)
        self.batch_service = batch_service
        self.compliance_service = compliance_service
        self.pdf_generator = PdfManifestGenerator()

    def generate_manifest(self, load: Load, driver_name: str, vehicle_plate: str) -> Dict[str, Any]:
        """
        Generates a PDF manifest for a given load.
        
        Args:
            load: The Load object
            driver_name: Name of the driver
            vehicle_plate: License plate of the vehicle
            
        Returns:
            Dictionary with 'pdf_path' and 'pdf_bytes'
        """
        try:
            # Gather data for PDF
            facility = self.facility_repo.get_by_id(load.origin_facility_id)
            site = self.site_repo.get_by_id(load.destination_site_id)
            batch = self.batch_service.get_batch_by_id(load.batch_id)
            plot = self.site_repo.get_active_plot(load.destination_site_id)
            
            # Calculate agronomic info for PDF
            agronomics = self.compliance_service.calculate_load_agronomics(load.batch_id, load.weight_net)
            site_area = plot.area_hectares if plot else 0
            rate_per_ha = (agronomics['total_n_kg'] / site_area) if site_area > 0 else 0
            
            load_data = {
                'origin_name': facility.name if facility else 'N/A',
                'dest_name': site.name if site else 'N/A',
                'driver_name': driver_name,
                'vehicle_plate': vehicle_plate,
                'batch_code': batch.batch_code if batch else 'N/A',
                'class_type': batch.class_type if batch else 'N/A',
                # Agronomic Data
                'pan_value': f"{agronomics['pan_kg_per_ton']:.2f}",
                'applied_nitrogen_kg': f"{agronomics['total_n_kg']:.2f}",
                'agronomic_rate': f"{rate_per_ha:.2f}"
            }
            
            pdf_bytes = self.pdf_generator.generate(load, load_data)
            
            # Save PDF to file system
            reports_dir = 'reports/manifests'
            os.makedirs(reports_dir, exist_ok=True)
            pdf_filename = f"manifiesto_{load.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(reports_dir, pdf_filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
                
            return {
                'pdf_path': pdf_path,
                'pdf_bytes': pdf_bytes
            }
                
        except Exception as e:
            # Log error but don't fail the dispatch completely if possible, 
            # though caller might decide to fail.
            print(f"Warning: PDF generation failed: {str(e)}")
            return {
                'pdf_path': None,
                'pdf_bytes': None
            }

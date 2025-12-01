from typing import Dict, Any, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from models.operations.load import Load
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator

class ManifestService:
    """
    Service for managing Load Manifests.
    Focused purely on document generation and code formatting.
    Database logic for creating loads has been moved to DispatchService.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.pdf_generator = PdfManifestGenerator()

    def generate_manifest_code(self) -> str:
        """
        Generates the next unique manifest code.
        """
        sequence = self.load_repo.get_next_manifest_sequence()
        current_year = datetime.now().year
        return f"MAN-{current_year}-{sequence:04d}"

    def generate_manifest_pdf(self, load_id: int) -> str:
        """
        Generates a PDF manifest for a given load ID.
        Returns the path to the generated file.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        # In a real implementation, we would fetch related entities (Driver, Vehicle, etc.)
        # to populate the PDF. For now, we assume the generator handles it or we pass minimal data.
        # This is a placeholder for the actual PDF generation call.
        
        # Example:
        # driver = self.driver_repo.get_by_id(load.driver_id)
        # vehicle = self.vehicle_repo.get_by_id(load.vehicle_id)
        # return self.pdf_generator.generate(load, driver, vehicle)
        
        return f"/tmp/manifest_{load.manifest_code}.pdf"

    # Legacy method support if needed, but prefer generate_manifest_pdf
    def generate_manifest(self, load_id: int) -> str:
        return self.generate_manifest_pdf(load_id)

            driver_name: Name of the driver
            vehicle_plate: License plate of the vehicle
            
        Returns:
            Dictionary with 'pdf_path' and 'pdf_bytes'
        """
        try:
            # Gather data for PDF
            facility = self.facility_repo.get_by_id(load.origin_facility_id) if hasattr(load, 'origin_facility_id') else None
            site = self.site_repo.get_by_id(load.destination_site_id) if hasattr(load, 'destination_site_id') else None
            batch = self.batch_service.get_batch_by_id(load.batch_id) if hasattr(load, 'batch_id') and load.batch_id else None
            plot = self.plot_repo.get_by_id(load.destination_plot_id) if hasattr(load, 'destination_plot_id') else None
            
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
                'driver_name': driver_name,
                'vehicle_plate': vehicle_plate,
                'weight_gross': load.gross_weight if hasattr(load, 'gross_weight') else load.weight_gross if hasattr(load, 'weight_gross') else 'Pendiente',
                'weight_tare': load.tare_weight if hasattr(load, 'tare_weight') else load.weight_tare if hasattr(load, 'weight_tare') else 'Pendiente',
                'weight_net': load.net_weight if hasattr(load, 'net_weight') else load.weight_net if hasattr(load, 'weight_net') else 'Pendiente',
                'pan_value': agronomics.get('pan_value', 'N/A'),
                'agronomic_rate': f"{rate_per_ha:.2f}" if rate_per_ha else 'N/A',
                'applied_nitrogen_kg': agronomics.get('total_n_kg', 'N/A')
            }
            
            # Generate PDF
            pdf_bytes = self.pdf_generator.generate(load, load_data)
            
            # Save to file (optional)
            import os
            reports_dir = 'reports/manifests'
            os.makedirs(reports_dir, exist_ok=True)
            pdf_path = f"{reports_dir}/manifest_{load.id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            return {
                'pdf_path': pdf_path,
                'pdf_bytes': pdf_bytes
            }
            
        except Exception as e:
            raise ValueError(f"Error generating manifest: {str(e)}")

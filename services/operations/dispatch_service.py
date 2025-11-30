from typing import Optional, Dict, Any
from datetime import datetime, date
import os
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.facility_repository import FacilityRepository
from repositories.site_repository import SiteRepository
from repositories.batch_repository import BatchRepository
from repositories.application_repository import ApplicationRepository
from services.operations.treatment_batch_service import TreatmentBatchService
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from models.operations.load import Load
from models.agronomy.application import NitrogenApplication
from domain.exceptions import TransitionException, ComplianceViolationError
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator

class DispatchService:
    """
    Handles the Dispatch Execution phase.
    Responsibilities:
    - Registering Dispatch (Gate Out)
    - Linking Containers and Batches (DS4 workflow)
    - Dispatching Trucks with Stock Management (Sprint 2 workflow)
    - Enforcing Compliance (Sprint 3)
    """
    def __init__(self, db_manager: DatabaseManager, batch_service: Optional[BatchService] = None):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = VehicleRepository(db_manager)
        self.facility_repo = FacilityRepository(db_manager)
        self.site_repo = SiteRepository(db_manager)
        self.batch_repo = BatchRepository(db_manager)
        self.application_repo = ApplicationRepository(db_manager)
        self.batch_service = batch_service  # Batch service for production lots
        
        # Initialize Compliance Service
        self.compliance_service = ComplianceService(
            self.site_repo, self.load_repo, self.batch_repo, self.application_repo
        )
        
        self.pdf_generator = PdfManifestGenerator()

    def dispatch_truck(
        self,
        batch_id: int,
        driver_id: int,
        vehicle_id: int,
        destination_site_id: int,
        origin_facility_id: int,
        weight_net: float,
        guide_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches a truck for the Sprint 2 operational flow.
        Creates load, reserves batch stock, and generates PDF manifest.
        Now includes Compliance Validation (Sprint 3).
        """
        # Validation 1: Check batch stock
        if not self.batch_service:
            raise ValueError("BatchService not configured")
        
        available = self.batch_service.get_batch_balance(batch_id)
        if weight_net > available:
            raise ValueError(
                f"Stock insuficiente. Disponible: {available} kg, Solicitado: {weight_net} kg"
            )
        
        # Validation 2: Check vehicle capacity
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehículo con ID {vehicle_id} no encontrado")
        
        if weight_net > vehicle.max_capacity:
            raise ValueError(
                f"Peso excede capacidad del vehículo. Capacidad: {vehicle.max_capacity} kg, Peso: {weight_net} kg"
            )
            
        # Validation 3: Compliance Check (Hard Constraints)
        # This will raise ComplianceViolationError if it fails
        try:
            self.compliance_service.validate_dispatch(batch_id, destination_site_id, weight_net)
        except ComplianceViolationError as e:
            # Re-raise with a clear prefix for UI handling
            raise ValueError(f"🚫 OPERACIÓN BLOQUEADA: {str(e)}")
        
        # Create load
        load = Load(
            id=None,
            origin_facility_id=origin_facility_id,
            destination_site_id=destination_site_id,
            batch_id=batch_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            weight_net=weight_net,
            guide_number=guide_number,
            status='InTransit',
            dispatch_time=datetime.now(),
            created_at=datetime.now()
        )
        
        # Save load to database
        created_load = self.load_repo.create_load(load)
        
        # Reserve stock from batch
        try:
            self.batch_service.reserve_tonnage(batch_id, weight_net)
        except ValueError as e:
            # Rollback: delete the created load
            self.load_repo.delete(created_load.id)
            raise ValueError(f"Error al reservar stock: {str(e)}")
            
            # Register Nitrogen Application (Sprint 3)
        try:
            # Calculate actual N applied
            agronomics = self.compliance_service.calculate_load_agronomics(batch_id, weight_net)
            nitrogen_kg = agronomics['total_n_kg']
            
            app = NitrogenApplication(
                id=None,
                site_id=destination_site_id,
                load_id=created_load.id,
                nitrogen_applied_kg=nitrogen_kg,
                application_date=date.today()
            )
            self.application_repo.add(app)
        except Exception as e:
            print(f"Warning: Failed to register nitrogen application: {str(e)}")
            # We don't rollback dispatch for this, but it should be logged
        
        # Generate PDF Manifest
        pdf_path = None
        try:
            # Gather data for PDF
            facility = self.facility_repo.get_by_id(origin_facility_id)
            site = self.site_repo.get_by_id(destination_site_id)
            batch = self.batch_service.get_batch_by_id(batch_id)
            plot = self.site_repo.get_active_plot(destination_site_id)
            
            # Calculate agronomic info for PDF
            agronomics = self.compliance_service.calculate_load_agronomics(batch_id, weight_net)
            site_area = plot.area_hectares if plot else 0
            rate_per_ha = (agronomics['total_n_kg'] / site_area) if site_area > 0 else 0
            
            load_data = {
                'origin_name': facility.name if facility else 'N/A',
                'dest_name': site.name if site else 'N/A',
                'driver_name': f'Driver #{driver_id}',  # Placeholder
                'vehicle_plate': vehicle.license_plate,
                'batch_code': batch.batch_code if batch else 'N/A',
                'class_type': batch.class_type if batch else 'N/A',
                # Agronomic Data
                'pan_value': f"{agronomics['pan_kg_per_ton']:.2f}",
                'applied_nitrogen_kg': f"{agronomics['total_n_kg']:.2f}",
                'agronomic_rate': f"{rate_per_ha:.2f}"
            }
            
            pdf_bytes = self.pdf_generator.generate(created_load, load_data)
            
            # Save PDF to file system
            reports_dir = 'reports/manifests'
            os.makedirs(reports_dir, exist_ok=True)
            pdf_filename = f"manifiesto_{created_load.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(reports_dir, pdf_filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
                
        except Exception as e:
            # Log error but don't fail the dispatch
            print(f"Warning: PDF generation failed: {str(e)}")
        
        return {
            'load_id': created_load.id,
            'guide_number': created_load.guide_number or f"GUIA-{created_load.id}",
            'pdf_path': pdf_path,
            'pdf_bytes': pdf_bytes if pdf_path else None
        }

    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, 
                          container_1_id: Optional[int] = None, container_2_id: Optional[int] = None) -> bool:
        """
        Registers the dispatch of the load (Start of Trip).
        Links containers and batches if applicable.
        This is for the DS4 treatment workflow.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            return False
            
        # State Transition Validation
        if load.status != 'Scheduled':
            raise TransitionException(f"Cannot dispatch load. Current status: {load.status}. Expected: 'Scheduled'.")
            
        load.ticket_number = ticket
        load.weight_gross = gross
        load.weight_tare = tare
        load.weight_net = gross - tare
        load.dispatch_time = datetime.now()
        load.status = 'In Transit'
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Link Containers & Batches (DS4 Logic) - Only if treatment_batch_service is available
        # Note: This part is for the DS4 workflow, not Sprint 2
        # For Sprint 2, we use dispatch_truck method instead
        
        return self.load_repo.update(load)


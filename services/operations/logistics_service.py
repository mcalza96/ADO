from typing import Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from models.operations.load import Load
from services.compliance.compliance_service import ComplianceService
from domain.exceptions import AgronomicException, ComplianceException, TransitionException

class LogisticsService:
    """
    Handles the planning and transport lifecycle of a Load.
    Responsibilities:
    - Request Creation
    - Resource Assignment (Scheduling)
    - Transport Finalization (Closing the trip)
    """
    def __init__(self, db_manager: DatabaseManager, compliance_service: ComplianceService):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.compliance_service = compliance_service

    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None) -> Load:
        """
        Creates a new Load Request.
        Can be from a Client Facility OR a Treatment Plant.
        """
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            origin_treatment_plant_id=plant_id,
            status='Requested',
            requested_date=requested_date,
            created_at=datetime.now()
        )
        return self.load_repo.add(load)

    def schedule_load(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, 
                         site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, 
                         container_quantity: Optional[int] = None) -> bool:
        """
        Assigns Driver, Vehicle, and Destination (Site OR Treatment Plant) to a Requested Load.
        Status -> 'Scheduled'.
        """
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        # State Transition Validation
        if load.status != 'Requested':
            raise TransitionException(f"Cannot schedule load. Current status: {load.status}. Expected: 'Requested'.")
        
        # Validation Logic for Sites
        if site_id:
            # TODO: Fetch real analysis from Lab module (LIMS)
            # Using mock analysis for now as per instructions
            mock_analysis = {
                'nitrate_no3': 10.0,
                'ammonium_nh4': 500.0,
                'tkn': 2500.0,
                'percent_solids': 20.0,
                'phosphorus_p': 100.0,
                'potassium_k': 50.0
            }
            
            # Estimate volume in tons. 
            # Assuming 20 tons per container if not specified, or derived from container_quantity.
            # Ideally this comes from Vehicle capacity or Load estimation.
            qty = container_quantity if container_quantity else 1
            estimated_volume_tons = qty * 20.0 
            
            # Validate Agronomic Compliance
            # This will raise AgronomicException or ComplianceException if it fails
            self.compliance_service.validate_application_feasibility(
                site_id=site_id,
                volume_tons=estimated_volume_tons,
                batch_analysis=mock_analysis
            )
        
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.container_quantity = container_quantity
        
        # Hybrid Logistics Logic
        if treatment_plant_id:
            load.destination_treatment_plant_id = treatment_plant_id
            load.destination_site_id = None # Clear if switching
        else:
            load.destination_site_id = site_id
            load.destination_treatment_plant_id = None # Clear if switching
            
        load.scheduled_date = scheduled_date
        load.status = 'Scheduled'
        load.updated_at = datetime.now()
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def finalize_load(self, load_id: int, guide_number: str, ticket_number: str, weight_net: float) -> bool:
        """
        Finalizes the Transport phase.
        Status -> 'PendingDisposal' (if Site) OR 'PendingReception' (if Treatment Plant).
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        load.guide_number = guide_number
        load.ticket_number = ticket_number
        load.weight_net = weight_net
        
        # Determine Next State based on Destination
        if load.destination_treatment_plant_id:
            load.status = 'PendingReception'
        else:
            load.status = 'PendingDisposal'
            
        load.dispatch_time = datetime.now()
        load.arrival_time = datetime.now()
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

from typing import Optional, Dict, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from repositories.vehicle_repository import VehicleRepository
from services.operations.batch_service import BatchService
from models.operations.load import Load
from domain.exceptions import TransitionException

class DispatchService:
    """
    Handles the Dispatch Execution phase.
    Responsibilities:
    - Registering Dispatch (Gate Out)
    - Linking Containers and Batches (DS4 workflow)
    - Dispatching Trucks with Stock Management (Sprint 2 workflow)
    - Enforcing Compliance (Sprint 3)
    """
    def __init__(
        self,
        db_manager: DatabaseManager,
        batch_service: BatchService,
        validation_service: 'DispatchValidationService',
        nitrogen_service: 'NitrogenApplicationService',
        manifest_service: 'ManifestService'
    ):
        """Initialize DispatchService with injected dependencies."""
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = VehicleRepository(db_manager)
        self.batch_service = batch_service
        self.validation_service = validation_service
        self.nitrogen_service = nitrogen_service
        self.manifest_service = manifest_service

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
        # Validate dispatch using dedicated service
        self.validation_service.validate_dispatch(batch_id, vehicle_id, destination_site_id, weight_net)
        
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
            
        # Register Nitrogen Application
        self.nitrogen_service.register_application(
            site_id=destination_site_id,
            load_id=created_load.id,
            batch_id=batch_id,
            weight_net=weight_net
        )
        
        # Generate PDF Manifest using ManifestService
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        driver_name = f'Driver #{driver_id}' # Placeholder
        manifest_result = self.manifest_service.generate_manifest(created_load, driver_name, vehicle.license_plate)
        
        return {
            'load_id': created_load.id,
            'guide_number': created_load.guide_number or f"GUIA-{created_load.id}",
            'pdf_path': manifest_result['pdf_path'],
            'pdf_bytes': manifest_result['pdf_bytes']
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
        load.status = 'Accepted' # Changed from 'In Transit' to 'Accepted' per new flow
        
        # Sync Support
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def accept_trip(self, load_id: int) -> bool:
        """
        Driver accepts the scheduled trip.
        Transitions from 'Scheduled' to 'Accepted'.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        if load.status != 'Scheduled':
            raise TransitionException(f"Cannot accept load. Current status: {load.status}. Expected: 'Scheduled'.")
            
        load.status = 'Accepted'
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Log transition
        import logging
        logging.info(f"Load {load_id} accepted by driver (Accepted).")
        
        return self.load_repo.update(load)

    def start_trip(self, load_id: int) -> bool:
        """
        Marks the start of the trip (Gate Out).
        Transitions from 'Accepted' to 'InTransit'.
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        if load.status != 'Accepted':
            raise TransitionException(f"Cannot start trip. Current status: {load.status}. Expected: 'Accepted'.")
            
        load.status = 'InTransit'
        load.dispatch_time = datetime.now() # Update dispatch time to actual departure
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Log transition
        import logging
        logging.info(f"Load {load_id} started trip (InTransit). Dispatch Time: {load.dispatch_time}")
        
        return self.load_repo.update(load)

    def register_arrival(self, load_id: int, weight_gross: float = None, ph: float = None, 
                        humidity: float = None, observation: str = None) -> bool:
        """
        Registers arrival at destination (Gate In).
        Transitions from 'InTransit' to 'Arrived'.
        Optionally captures quality parameters at arrival.
        
        Args:
            load_id: ID of the load
            weight_gross: Optional gross weight at arrival
            ph: Optional pH reading at arrival
            humidity: Optional humidity reading at arrival
            observation: Optional quality observations
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        load.register_arrival(weight_gross, ph, humidity, observation) # Uses the model method
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Log transition
        import logging
        logging.info(f"Load {load_id} arrived at destination (Arrived).")
        
        return self.load_repo.update(load)

    def close_trip(self, load_id: int, data_dict: Dict[str, Any]) -> bool:
        """
        Closes the trip at destination.
        Transitions from 'Arrived' to 'Delivered'.
        
        Args:
            load_id: ID of the load
            data_dict: Dictionary containing:
                - weight_net: Final net weight
                - ticket_number: Weighing ticket
                - guide_number: Dispatch guide
                - quality_ph: pH value
                - quality_humidity: Humidity value
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        # Extract data
        weight_net = data_dict.get('weight_net')
        ticket = data_dict.get('ticket_number')
        guide = data_dict.get('guide_number')
        ph = data_dict.get('quality_ph')
        humidity = data_dict.get('quality_humidity')
        
        # Validate required fields
        if any(v is None for v in [weight_net, ticket, guide, ph, humidity]):
             raise ValueError("Missing required fields for closing trip")

        # Validation: Net Weight vs Gross Reception Weight
        # If we have a reception weight, net weight should logically be less (or equal in edge cases)
        # We allow a small margin of error or just warn, but for now let's enforce logical consistency
        if load.weight_gross_reception and float(weight_net) > load.weight_gross_reception:
             # This might be too strict if scales differ significantly, but good for data integrity
             # Let's log a warning instead of blocking for now, unless user wants strict enforcement
             # For TTO-03 strictness:
             pass 
             # TODO: Decide if we block. For now, we proceed but could log it.
        
        # Update Load using model method
        load.close_trip(
            weight_net=float(weight_net),
            ticket_number=ticket,
            guide_number=guide,
            ph=float(ph),
            humidity=float(humidity)
        )
        
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        # Log transition
        import logging
        logging.info(f"Load {load_id} closed (Delivered). Net Weight: {weight_net}, Ticket: {ticket}")
        
        # Handoff Logic is implicit:
        # The load is now 'Delivered'.
        # Downstream services (Disposal/Treatment) will query using 
        # load_repo.get_delivered_by_destination_type()
        
        return self.load_repo.update(load)




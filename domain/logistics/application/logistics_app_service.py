from typing import Optional, Dict, Any, List
from domain.logistics.dtos import DispatchExecutionDTO, ReceptionRequestDTO, PickupRequestDTO
from domain.logistics.services.dispatch_service import LogisticsDomainService
from domain.processing.services.container_tracking_service import ContainerTrackingService
from domain.logistics.entities.load import Load
from domain.logistics.services.manifest_service import ManifestService
from infrastructure.events.event_bus import EventBus, EventTypes

class LogisticsApplicationService:
    """
    Application Service for Logistics Operations.
    Orchestrates Dispatch, Reception, and Planning processes.
    """
    def __init__(
        self, 
        logistics_service: LogisticsDomainService, 
        manifest_service: ManifestService,
        event_bus: EventBus,
        container_tracking_service: Optional[ContainerTrackingService] = None
    ):
        self.logistics_service = logistics_service
        self.manifest_service = manifest_service
        self.event_bus = event_bus
        self.container_tracking_service = container_tracking_service

    # --- Dispatch (Gate Out) ---
    def execute_dispatch(self, dto: DispatchExecutionDTO) -> None:
        """
        Executes the dispatch (Gate Out) process.
        
        Args:
            dto: Validated dispatch data
        """
        # 1. Prepare data dict for legacy service
        # The domain service expects a dict with specific keys
        data = {
            'ticket_number': dto.ticket_number,
            'guide_number': dto.guide_number,
            'weight_net': dto.weight_net,
            'quality_ph': dto.quality_ph,
            'quality_humidity': dto.quality_humidity
        }
        
        # 2. Call domain service to close the trip
        self.logistics_service.close_trip(dto.load_id, data)
        
        # 3. Generate Manifest
        try:
            self.manifest_service.generate(dto.load_id)
        except Exception as e:
            # Log error but don't fail dispatch
            print(f"Error generating manifest: {e}")
            
        # 4. Publish Event
        self.event_bus.publish(EventTypes.LOAD_DISPATCHED, {'load_id': dto.load_id})
        
        # 5. Handle container tracking if needed (for treatment plants)
        if self.container_tracking_service:
            if dto.container_1_id:
                self.container_tracking_service.mark_as_dispatched(
                    record_id=dto.container_1_id,
                    load_id=dto.load_id,
                    container_position=1
                )
            
            if dto.container_2_id:
                self.container_tracking_service.mark_as_dispatched(
                    record_id=dto.container_2_id,
                    load_id=dto.load_id,
                    container_position=2
                )

    # --- Reception (Gate In) ---
    def execute_reception(self, dto: ReceptionRequestDTO) -> None:
        """
        Executes the reception (Gate In) process.
        
        Args:
            dto: Validated reception data
        """
        self.logistics_service.register_arrival(
            load_id=dto.load_id,
            weight_gross=dto.weight_gross,
            ph=dto.ph,
            humidity=dto.humidity,
            observation=dto.observation
        )

    def get_active_loads(self) -> List[Load]:
        """Get all loads currently in transit."""
        return self.logistics_service.get_in_transit_loads()

    # --- Planning (Pickup Requests) ---
    def create_pickup_request(self, dto: PickupRequestDTO) -> Load:
        """
        Creates a new pickup request.
        
        Args:
            dto: Validated request data
        """
        return self.logistics_service.create_request(
            facility_id=dto.facility_id,
            requested_date=dto.requested_date,
            weight_estimated=dto.weight_estimated,
            notes=dto.notes
        )

    def get_pending_pickup_requests(self) -> List[Load]:
        """Get all pending pickup requests."""
        return self.logistics_service.get_planning_loads(status='REQUESTED')

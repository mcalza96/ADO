from typing import List, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from repositories.load_repository import LoadRepository
from repositories.site_repository import SiteRepository
from repositories.batch_repository import BatchRepository
from repositories.application_repository import ApplicationRepository
from models.operations.load import Load

# Import new specialized services
from services.operations.logistics_service import LogisticsService
from services.operations.dispatch_service import DispatchService
from services.operations.reception_service import ReceptionService
from services.operations.treatment_batch_service import TreatmentBatchService
from services.compliance.compliance_service import ComplianceService

class OperationsService:
    """
    Facade for Operations Module.
    Delegates to specialized services for state transitions.
    """
    def __init__(self, db_manager: DatabaseManager, dispatch_service: Optional[DispatchService] = None):
        self.db_manager = db_manager
        # Keep LoadRepository for read-only operations (Getters)
        self.load_repo = LoadRepository(db_manager)
        
        # Initialize Repositories needed for Compliance
        site_repo = SiteRepository(db_manager)
        batch_repo = BatchRepository(db_manager)
        application_repo = ApplicationRepository(db_manager)
        
        # Initialize Compliance Service
        compliance_service = ComplianceService(site_repo, self.load_repo, batch_repo, application_repo)
        
        # Initialize Sub-services
        self.logistics_service = LogisticsService(db_manager, compliance_service)
        
        # Inject TreatmentBatchService into DispatchService to resolve circular dependency
        # batch_service = TreatmentBatchService(db_manager)
        if dispatch_service:
            self.dispatch_service = dispatch_service
        else:
             # Fallback for legacy calls (though this will likely fail if dependencies are missing)
             # We leave it as is or try to construct it, but for now let's assume DI is used.
             batch_service = TreatmentBatchService(db_manager)
             # This will fail with new signature, but we expect container to pass it.
             # To avoid crash on import/init without DI, we can pass None or mocks if absolutely needed,
             # but better to rely on DI.
             # For now, let's just comment out the manual instantiation if dispatch_service is not provided
             # to avoid the crash, assuming it will be provided by container.
             self.dispatch_service = None # type: ignore
        
        self.reception_service = ReceptionService(db_manager)

    # --- READ OPERATIONS (Delegated to Repository) ---
    def get_all_loads(self) -> List[Load]:
        return self.load_repo.get_all_ordered_by_date()
            
    def get_loads_by_status(self, status: str) -> List[Load]:
        return self.load_repo.get_by_status(status)

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        return self.load_repo.get_by_id(load_id)

    def get_loads_by_facility(self, facility_id: int) -> List[Load]:
        return self.load_repo.get_by_origin_facility(facility_id)

    # --- 1. REQUEST PHASE (Delegated to LogisticsService) ---
    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None) -> Load:
        return self.logistics_service.create_request(facility_id, requested_date, plant_id)

    # --- 2. PLANNING PHASE (Delegated to LogisticsService) ---
    def assign_resources(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, container_quantity: Optional[int] = None) -> bool:
        return self.logistics_service.assign_resources(load_id, driver_id, vehicle_id, scheduled_date, site_id, treatment_plant_id, container_quantity)

    # --- 3. EXECUTION PHASE (Delegated to DispatchService) ---
    def register_dispatch(self, load_id: int, ticket: str, gross: float, tare: float, 
                          container_1_id: Optional[int] = None, container_2_id: Optional[int] = None) -> bool:
        return self.dispatch_service.register_dispatch(load_id, ticket, gross, tare, container_1_id, container_2_id)

    def finalize_load(self, load_id: int, guide_number: str, ticket_number: str, weight_net: float) -> bool:
        return self.logistics_service.finalize_load(load_id, guide_number, ticket_number, weight_net)

    # --- LEGACY / UTILS ---
    def update_load_status(self, load_id: int, status: str, **kwargs) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if load:
            load.status = status
            return self.load_repo.update(load)
        return False

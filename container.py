"""
Dependency Injection Container for the Biosolids ERP.

This module provides a centralized dependency injection container that manages
the lifecycle of database connections, repositories, and services. Using Streamlit's
@st.cache_resource decorator ensures singleton behavior, preventing duplicate
database connections on each user interaction.

Phase 4: UI Decoupling - The UI layer should not instantiate DatabaseManager or
services directly. Instead, it should request ready-to-use services from this container.
"""

import streamlit as st
from types import SimpleNamespace
from database.db_manager import DatabaseManager
from repositories.site_repository import SiteRepository
from repositories.plot_repository import PlotRepository
from repositories.load_repository import LoadRepository
from repositories.site_event_repository import SiteEventRepository
from repositories.user_repository import UserRepository
from repositories.batch_repository import BatchRepository
from repositories.application_repository import ApplicationRepository
from services.masters.location_service import LocationService
from services.operations.disposal_execution import DisposalExecutionService
from services.masters.transport_service import TransportService
from services.operations.dispatch_service import DispatchService
from services.auth_service import AuthService


from services.operations.site_preparation_service import SitePreparationService
from services.operations.manifest_service import ManifestService
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from services.operations.dispatch_validation_service import DispatchValidationService
from services.operations.nitrogen_application_service import NitrogenApplicationService
from services.operations.reception_service import ReceptionService
from repositories.vehicle_repository import VehicleRepository
from services.operations.logistics_service import LogisticsService
from services.operations.treatment_reception import TreatmentReceptionService
from services.operations.treatment_batch_service import TreatmentBatchService
from services.masters.client_service import ClientService
from services.masters.treatment_plant_service import TreatmentPlantService
from services.masters.container_service import ContainerService
from services.masters.disposal_service import DisposalService as MasterDisposalService
from services.masters.treatment_service import TreatmentService
from services.operations_service import OperationsService
from services.masters.contractor_service import ContractorService
from services.operations.dashboard_service import DashboardService

@st.cache_resource
def get_container() -> SimpleNamespace:
    """
    Creates and returns a singleton dependency injection container.
    
    This function is decorated with @st.cache_resource to ensure that it only
    executes once per Streamlit session, maintaining a single DatabaseManager
    instance and preventing connection duplication.
    
    Returns:
        SimpleNamespace: A container object with the following attributes:
            - db_manager: DatabaseManager instance
            - location_service: LocationService instance
            - disposal_service: DisposalExecutionService instance
            - transport_service: TransportService instance
            - facility_service: FacilityService instance
            
    Example:
        >>> services = get_container()
        >>> sites = services.location_service.get_all_sites()
        >>> pending = services.disposal_service.get_pending_disposal_loads(site_id)
    """
    # Initialize DatabaseManager using centralized configuration
    db_manager = DatabaseManager()
    
    # Initialize Repositories
    site_repo = SiteRepository(db_manager)
    plot_repo = PlotRepository(db_manager)
    load_repo = LoadRepository(db_manager)
    site_event_repo = SiteEventRepository(db_manager)
    user_repo = UserRepository(db_manager)
    batch_repo = BatchRepository(db_manager)
    application_repo = ApplicationRepository(db_manager)
    vehicle_repo = VehicleRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(site_repo, plot_repo)
    batch_service = BatchService(db_manager)
    
    # Compliance Service (needed for Manifest and Validation)
    compliance_service = ComplianceService(
        site_repo, load_repo, batch_repo, application_repo
    )
    
    # Validation and Nitrogen Services
    dispatch_validation_service = DispatchValidationService(
        vehicle_repo, batch_service, compliance_service
    )
    nitrogen_app_service = NitrogenApplicationService(
        application_repo, compliance_service
    )
    
    manifest_service = ManifestService(db_manager, batch_service, compliance_service)
    site_prep_service = SitePreparationService(db_manager)
    
    disposal_service = DisposalExecutionService(db_manager)
    auth_service = AuthService(user_repo)
    transport_service = TransportService(db_manager)
    
    # DispatchService with all dependencies injected
    dispatch_service = DispatchService(
        db_manager,
        batch_service,
        dispatch_validation_service,
        nitrogen_app_service,
        manifest_service
    )
    
    # ReceptionService for TTO-02/TTO-03 workflows
    reception_service = ReceptionService(db_manager, batch_service)
    
    # LogisticsService for planning workflows
    logistics_service = LogisticsService(db_manager, compliance_service)
    
    # Treatment Reception Service
    treatment_reception_service = TreatmentReceptionService(db_manager)
    
    # Treatment Batch Service (for DS4 monitoring)
    treatment_batch_service = TreatmentBatchService(db_manager)
    
    # Master Services
    client_service = ClientService(db_manager)
    contractor_service = ContractorService(db_manager)
    treatment_plant_service = TreatmentPlantService(db_manager)
    container_service = ContainerService(db_manager)
    master_disposal_service = MasterDisposalService(db_manager)
    treatment_service = TreatmentService(db_manager)
    
    # Operations Facade (agregates multiple operation services)
    operations_service = OperationsService(db_manager, dispatch_service=dispatch_service)
    
    # Dashboard Service
    dashboard_service = DashboardService(db_manager)
    
    # Return a simple container object with services as attributes
    return SimpleNamespace(
        db_manager=db_manager,
        location_service=location_service,
        disposal_service=disposal_service,
        auth_service=auth_service,
        transport_service=transport_service,
        dispatch_service=dispatch_service,
        site_prep_service=site_prep_service,
        manifest_service=manifest_service,
        batch_service=batch_service,
        treatment_batch_service=treatment_batch_service,
        reception_service=reception_service,
        logistics_service=logistics_service,
        treatment_reception_service=treatment_reception_service,
        client_service=client_service,
        contractor_service=contractor_service,
        treatment_plant_service=treatment_plant_service,
        container_service=container_service,
        master_disposal_service=master_disposal_service,
        treatment_service=treatment_service,
        operations_service=operations_service,
        dashboard_service=dashboard_service,
        compliance_service=compliance_service,
        dispatch_validation_service=dispatch_validation_service,
        nitrogen_app_service=nitrogen_app_service
    )

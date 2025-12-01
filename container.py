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
from repositories.nitrogen_application_repository import NitrogenApplicationRepository
from repositories.client_repository import ClientRepository
from repositories.contractor_repository import ContractorRepository
from repositories.driver_repository import DriverRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.reporting_repository import ReportingRepository

from services.masters.location_service import LocationService
from services.operations.disposal_execution_service import DisposalExecutionService
from services.operations.dispatch_service import DispatchService
from services.auth_service import AuthService


from services.operations.site_preparation_service import SitePreparationService
from services.operations.manifest_service import ManifestService
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from services.operations.nitrogen_application_service import NitrogenApplicationService
from services.operations.reception_service import ReceptionService
from services.operations.logistics_service import LogisticsService
from services.operations.treatment_reception import TreatmentReceptionService
from services.operations.treatment_batch_service import TreatmentBatchService
from services.masters.client_service import ClientService
from services.masters.treatment_plant_service import TreatmentPlantService
from services.masters.container_service import ContainerService
from services.masters.disposal_service import DisposalService as MasterDisposalService
from services.masters.treatment_service import TreatmentService
from services.masters.contractor_service import ContractorService
from services.masters.driver_service import DriverService
from services.masters.vehicle_service import VehicleService
from services.reporting.reporting_service import ReportingService
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
    application_repo = NitrogenApplicationRepository(db_manager)
    vehicle_repo = VehicleRepository(db_manager)
    client_repo = ClientRepository(db_manager)
    contractor_repo = ContractorRepository(db_manager)
    driver_repo = DriverRepository(db_manager)
    reporting_repo = ReportingRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(site_repo, plot_repo)
    batch_service = BatchService(db_manager)
    
    # Compliance Service (needed for Manifest and Validation)
    compliance_service = ComplianceService(
        site_repo, load_repo, batch_repo, application_repo
    )
    
    # Validation and Nitrogen Services
    nitrogen_app_service = NitrogenApplicationService(
        application_repo, compliance_service
    )
    
    # ManifestService instantiated with updated signature
    manifest_service = ManifestService(db_manager, batch_service, compliance_service)
    site_prep_service = SitePreparationService(db_manager)
    
    disposal_service = DisposalExecutionService(db_manager)
    auth_service = AuthService(user_repo)
    
    # DispatchService with all dependencies injected
    dispatch_service = DispatchService(
        db_manager,
        batch_service,
        compliance_service,
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
    client_service = ClientService(client_repo)
    contractor_service = ContractorService(contractor_repo)
    driver_service = DriverService(driver_repo, contractor_repo)
    vehicle_service = VehicleService(vehicle_repo)
    treatment_plant_service = TreatmentPlantService(db_manager)
    container_service = ContainerService(db_manager)
    master_disposal_service = MasterDisposalService(db_manager)
    treatment_service = TreatmentService(db_manager)
    
    # Reporting Service
    reporting_service = ReportingService(reporting_repo)
    
    # Dashboard Service
    dashboard_service = DashboardService(db_manager)
    
    # Return a simple container object with services as attributes
    return SimpleNamespace(
        db_manager=db_manager,
        location_service=location_service,
        disposal_service=disposal_service,
        auth_service=auth_service,
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
        driver_service=driver_service,
        vehicle_service=vehicle_service,
        treatment_plant_service=treatment_plant_service,
        container_service=container_service,
        master_disposal_service=master_disposal_service,
        treatment_service=treatment_service,
        dashboard_service=dashboard_service,
        compliance_service=compliance_service,
        nitrogen_app_service=nitrogen_app_service,
        reporting_service=reporting_service
    )

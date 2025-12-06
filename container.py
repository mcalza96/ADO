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
from infrastructure.persistence.database_manager import DatabaseManager
from domain.logistics.repositories.load_repository import LoadRepository
from infrastructure.persistence.reporting_repository import ReportingRepository
from infrastructure.persistence.generic_repository import BaseRepository

# Models for Generic Repositories
from domain.shared.entities.location import Site, Plot
from domain.disposal.entities.site_event import SiteEvent
from domain.shared.entities.user import User
from domain.disposal.entities.application import NitrogenApplication
from domain.shared.entities.client import Client
from domain.logistics.entities.contractor import Contractor
from domain.logistics.entities.driver import Driver
from domain.logistics.entities.vehicle import Vehicle
from domain.processing.entities.treatment_plant import TreatmentPlant
from domain.processing.entities.facility import Facility
from domain.logistics.entities.container import Container

from domain.disposal.services.location_service import LocationService
from domain.logistics.services.dispatch_service import LogisticsDomainService
from domain.logistics.services.load_state_service import LoadStateService
from domain.logistics.services.load_planning_service import LoadPlanningService
from domain.logistics.services.load_dispatch_service import LoadDispatchService
from domain.logistics.services.load_reception_service import LoadReceptionService
from domain.logistics.services.trip_linking_service import TripLinkingService
from domain.logistics.application.logistics_app_service import LogisticsApplicationService
from domain.logistics.services.pickup_request_service import PickupRequestService
from domain.disposal.services.agronomy_service import AgronomyDomainService
from domain.disposal.services.disposal_master_service import DisposalService
from domain.shared.services.auth_service import AuthService
from domain.logistics.services.manifest_service import ManifestService
from domain.processing.services.container_tracking_service import ContainerTrackingService
from domain.shared.services.compliance_service import ComplianceService
from domain.processing.services.reception_service import TreatmentReceptionService
from domain.processing.services.treatment_master_service import TreatmentService
from domain.shared.generic_crud_service import GenericCrudService
from domain.disposal.application.disposal_app_service import DisposalApplicationService
from domain.processing.application.treatment_app_service import TreatmentApplicationService
from infrastructure.reporting.reporting_service import ReportingService
from infrastructure.reporting.dashboard_service import DashboardService
from ui.utils.task_resolver import TaskResolver

# Event Bus
from infrastructure.events.event_bus import EventBus, EventTypes

# Machinery & Field Reception
from domain.agronomy.services.machinery_service import MachineryService
from domain.agronomy.repositories.machine_log_repository import MachineLogRepository
from domain.agronomy.services.field_reception_handler import FieldReceptionHandler

# Financial Reporting (Phase 5)
from domain.finance.repositories.economic_indicators_repository import EconomicIndicatorsRepository
from domain.finance.repositories.proforma_repository import ProformaRepository
from domain.finance.repositories.contractor_tariffs_repository import ContractorTariffsRepository
from domain.finance.repositories.client_tariffs_repository import ClientTariffsRepository
from domain.finance.repositories.disposal_site_tariffs_repository import DisposalSiteTariffsRepository
from domain.logistics.repositories.distance_matrix_repository import DistanceMatrixRepository
from domain.finance.services.financial_reporting_service import FinancialReportingService

# Satellite Modules (Phase 3)
from domain.maintenance.services.maintenance_listener import MaintenanceListener
from domain.compliance.services.compliance_listener import ComplianceListener
from domain.finance.services.costing_listener import CostingListener

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
    
    # Initialize EventBus as singleton
    event_bus = EventBus()
    
    # Initialize Repositories
    # Generic Repositories
    site_repo = BaseRepository(db_manager, Site, "sites")
    plot_repo = BaseRepository(db_manager, Plot, "plots")
    site_event_repo = BaseRepository(db_manager, SiteEvent, "site_events")
    user_repo = BaseRepository(db_manager, User, "users")
    application_repo = BaseRepository(db_manager, NitrogenApplication, "nitrogen_applications")
    vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
    client_repo = BaseRepository(db_manager, Client, "clients")
    facility_repo = BaseRepository(db_manager, Facility, "facilities")
    contractor_repo = BaseRepository(db_manager, Contractor, "contractors")
    driver_repo = BaseRepository(db_manager, Driver, "drivers")
    
    # Specific Repositories (Custom SQL or Logic)
    load_repo = LoadRepository(db_manager)
    reporting_repo = ReportingRepository(db_manager)
    machine_log_repo = MachineLogRepository(db_manager)
    
    # Financial Repositories
    economic_indicators_repo = EconomicIndicatorsRepository(db_manager)
    proforma_repo = ProformaRepository(db_manager)
    contractor_tariffs_repo = ContractorTariffsRepository(db_manager)
    client_tariffs_repo = ClientTariffsRepository(db_manager)
    disposal_site_tariffs_repo = DisposalSiteTariffsRepository(db_manager)
    distance_matrix_repo = DistanceMatrixRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(site_repo, plot_repo)
    
    # Compliance Service (needed for Manifest and Validation)
    compliance_service = ComplianceService(
        site_repo, load_repo, application_repo
    )
    
    # Agronomy Domain Service
    agronomy_service = AgronomyDomainService(db_manager, compliance_service)
    
    # Manifest Service
    manifest_service = ManifestService(db_manager, compliance_service)

    # --- NEW: Specialized Logistics Services (Refactored from LogisticsDomainService) ---
    
    # 1. State Management Service
    load_state_service = LoadStateService(
        db_manager=db_manager,
        event_bus=event_bus
    )
    
    # 2. Planning Service
    load_planning_service = LoadPlanningService(db_manager=db_manager)
    
    # 3. Dispatch Service
    load_dispatch_service = LoadDispatchService(db_manager=db_manager)
    
    # 4. Reception Service
    load_reception_service = LoadReceptionService(db_manager=db_manager)
    
    # 5. Trip Linking Service
    trip_linking_service = TripLinkingService(db_manager=db_manager)

    # Logistics Domain Service (Legacy - maintained for backward compatibility)
    # TODO: Gradually migrate UI to use specialized services above
    logistics_service = LogisticsDomainService(
        db_manager,
        compliance_service,
        agronomy_service,
    )
    
    # Machinery Service
    machinery_service = MachineryService(db_manager, event_bus)
    
    # Field Reception Handler (Cross-domain integration)
    field_handler = FieldReceptionHandler(db_manager)
    
    # Satellite Listeners (Phase 3)
    maintenance_listener = MaintenanceListener(db_manager)
    compliance_listener = ComplianceListener(db_manager)
    costing_listener = CostingListener(db_manager)
    
    # Register Event Listeners
    # 1. Agronomy
    event_bus.subscribe(EventTypes.LOAD_ARRIVED_AT_FIELD, field_handler.handle_load_arrived_at_field)
    
    # 2. Maintenance
    event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, maintenance_listener.handle_load_completed)
    event_bus.subscribe(EventTypes.MACHINE_WORK_RECORDED, maintenance_listener.handle_machine_work)
    
    # 3. Compliance
    event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, compliance_listener.handle_load_completed)
    
    # 4. Finance
    event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, costing_listener.handle_load_completed)
    event_bus.subscribe(EventTypes.MACHINE_WORK_RECORDED, costing_listener.handle_machine_work)
    
    # Master Disposal Service - debe crearse antes del alias
    master_disposal_service = DisposalService(db_manager)
    
    # Disposal Application Service
    disposal_app_service = DisposalApplicationService(master_disposal_service)
    
    # Aliases for backward compatibility (if needed during transition)
    dispatch_service = logistics_service
    reception_service = logistics_service
    disposal_service = master_disposal_service  # Usar MasterDisposalService que tiene register_arrival
    site_prep_service = agronomy_service
    nitrogen_app_service = agronomy_service
    
    # Treatment Reception Service
    treatment_reception_service = TreatmentReceptionService(db_manager)
    
    # Treatment Application Service
    treatment_app_service = TreatmentApplicationService(treatment_reception_service)
    
    # Master Services (using GenericCrudService)
    client_service = GenericCrudService(client_repo)
    facility_service = GenericCrudService(facility_repo)
    contractor_service = GenericCrudService(contractor_repo)
    driver_service = GenericCrudService(driver_repo)
    vehicle_service = GenericCrudService(vehicle_repo)
    treatment_plant_service = GenericCrudService(BaseRepository(db_manager, TreatmentPlant, "treatment_plants"))
    container_service = GenericCrudService(BaseRepository(db_manager, Container, "containers"))
    treatment_service = TreatmentService(db_manager)
    
    # Reporting Service
    reporting_service = ReportingService(reporting_repo)
    
    # Dashboard Service
    dashboard_service = DashboardService(db_manager)
    
    # Auth Service
    auth_service = AuthService(user_repo)
    
    # Pickup Request Service (Client requests)
    pickup_request_service = PickupRequestService(db_manager, facility_repo)

    # Container Tracking Service (DS4 container filling with pH measurements)
    container_tracking_service = ContainerTrackingService(db_manager)

    # Application Services
    logistics_app_service = LogisticsApplicationService(
        logistics_service=logistics_service,
        manifest_service=manifest_service,
        event_bus=event_bus,
        container_tracking_service=container_tracking_service
    )

    # Task Resolver (UI Service)
    task_resolver = TaskResolver(load_repo, machine_log_repo)
    
    # Financial Reporting Service
    financial_reporting_service = FinancialReportingService(
        load_repo=load_repo,
        economic_repo=economic_indicators_repo,
        contractor_tariffs_repo=contractor_tariffs_repo,
        client_tariffs_repo=client_tariffs_repo,
        distance_repo=distance_matrix_repo,
        disposal_site_tariffs_repo=disposal_site_tariffs_repo,
        proforma_repo=proforma_repo  # New: Proforma repository for payment states
    )
    
    # Financial Export Service
    from infrastructure.reporting.financial_export_service import FinancialExportService
    financial_export_service = FinancialExportService()
    
    # Accounting Closure Service
    from domain.finance.services.accounting_closure_service import AccountingClosureService
    accounting_closure_service = AccountingClosureService(
        economic_repo=economic_indicators_repo,
        load_repo=load_repo,
        reporting_service=financial_reporting_service
    )
    
    # Return a simple container object with services as attributes
    return SimpleNamespace(
        db_manager=db_manager,
        event_bus=event_bus,
        location_service=location_service,
        disposal_service=disposal_service,
        disposal_app_service=disposal_app_service,
        auth_service=auth_service,
        dispatch_service=dispatch_service,
        site_prep_service=site_prep_service,
        manifest_service=manifest_service,
        reception_service=reception_service,
        logistics_service=logistics_service,
        logistics_app_service=logistics_app_service,
        
        # NEW: Specialized Logistics Services
        load_state_service=load_state_service,
        load_planning_service=load_planning_service,
        load_dispatch_service=load_dispatch_service,
        load_reception_service=load_reception_service,
        trip_linking_service=trip_linking_service,
        
        treatment_reception_service=treatment_reception_service,
        treatment_app_service=treatment_app_service,
        client_service=client_service,
        facility_service=facility_service,
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
        reporting_service=reporting_service,

        agronomy_service=agronomy_service,
        machinery_service=machinery_service,  # New service
        task_resolver=task_resolver,
        pickup_request_service=pickup_request_service,  # Client pickup requests
        container_tracking_service=container_tracking_service,  # DS4 container tracking
        financial_reporting_service=financial_reporting_service,  # Financial settlement reports
        financial_export_service=financial_export_service, # Financial Excel/PDF export
        accounting_closure_service=accounting_closure_service, # Accounting period closure
        
        # Financial Repositories (exposed for UI configuration)
        economic_indicators_repo=economic_indicators_repo,
        proforma_repo=proforma_repo,  # New: Proforma master repository
        distance_matrix_repo=distance_matrix_repo,
        contractor_tariffs_repo=contractor_tariffs_repo,
        client_tariffs_repo=client_tariffs_repo,
    )


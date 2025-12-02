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
from domain.logistics.repositories.load_repository import LoadRepository
from domain.processing.repositories.batch_repository import BatchRepository
from repositories.reporting_repository import ReportingRepository
from database.repository import BaseRepository

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
from domain.disposal.services.agronomy_service import AgronomyDomainService
from domain.shared.services.auth_service import AuthService
from services.operations.manifest_service import ManifestService
from domain.shared.services.compliance_service import ComplianceService
from domain.processing.services.reception_service import TreatmentReceptionService
from domain.processing.services.batch_service import TreatmentBatchService
from domain.shared.generic_crud_service import GenericCrudService
from domain.disposal.services.disposal_master_service import DisposalService as MasterDisposalService
from domain.processing.services.treatment_master_service import TreatmentService
from services.reporting.reporting_service import ReportingService
from services.operations.dashboard_service import DashboardService
from services.ui.task_resolver import TaskResolver

# Event Bus
from services.common.event_bus import EventBus, EventTypes

# Machinery & Field Reception
from domain.agronomy.services.machinery_service import MachineryService
from domain.agronomy.repositories.machine_log_repository import MachineLogRepository
from domain.agronomy.services.field_reception_handler import FieldReceptionHandler

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
    batch_repo = BatchRepository(db_manager)
    reporting_repo = ReportingRepository(db_manager)
    machine_log_repo = MachineLogRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(site_repo, plot_repo)
    batch_service = TreatmentBatchService(db_manager)
    
    # Compliance Service (needed for Manifest and Validation)
    compliance_service = ComplianceService(
        site_repo, load_repo, batch_repo, application_repo
    )
    
    # Agronomy Domain Service
    agronomy_service = AgronomyDomainService(db_manager, compliance_service)
    
    # Manifest Service
    manifest_service = ManifestService(db_manager, batch_service, compliance_service)

    # Logistics Domain Service
    logistics_service = LogisticsDomainService(
        db_manager,
        batch_service,
        compliance_service,
        agronomy_service,
        manifest_service,
        event_bus=event_bus  # Inject EventBus
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
    
    # Aliases for backward compatibility (if needed during transition)
    dispatch_service = logistics_service
    reception_service = logistics_service
    disposal_service = agronomy_service
    site_prep_service = agronomy_service
    nitrogen_app_service = agronomy_service
    
    # Treatment Reception Service
    treatment_reception_service = TreatmentReceptionService(db_manager)
    
    # Treatment Batch Service (for DS4 monitoring)
    treatment_batch_service = TreatmentBatchService(db_manager)
    
    # Master Services (using GenericCrudService)
    client_service = GenericCrudService(client_repo)
    facility_service = GenericCrudService(facility_repo)
    contractor_service = GenericCrudService(contractor_repo)
    driver_service = GenericCrudService(driver_repo)
    vehicle_service = GenericCrudService(vehicle_repo)
    treatment_plant_service = GenericCrudService(BaseRepository(db_manager, TreatmentPlant, "treatment_plants"))
    container_service = GenericCrudService(BaseRepository(db_manager, Container, "containers"))
    master_disposal_service = MasterDisposalService(db_manager)
    treatment_service = TreatmentService(db_manager)
    
    # Reporting Service
    reporting_service = ReportingService(reporting_repo)
    
    # Dashboard Service
    dashboard_service = DashboardService(db_manager)
    
    # Auth Service
    auth_service = AuthService(user_repo)

    # Task Resolver (UI Service)
    task_resolver = TaskResolver(load_repo, machine_log_repo)
    
    # Return a simple container object with services as attributes
    return SimpleNamespace(
        db_manager=db_manager,
        event_bus=event_bus,
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
    )

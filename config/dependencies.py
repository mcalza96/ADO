"""
Modular Dependency Injection System.

This module provides bounded context-based container classes that organize
dependencies by domain area, making the system more maintainable and scalable.

Usage:
    from config.dependencies import get_container
    container = get_container()
    container.logistics.dispatch_service.create_request(...)
"""

from types import SimpleNamespace
from typing import Optional
import streamlit as st

from database.db_manager import DatabaseManager
from services.common.event_bus import EventBus


class LogisticsContainer:
    """
    Container for Logistics bounded context.
    
    Responsibilities:
    - Load management (create, dispatch, track)
    - Vehicle and driver assignment
    - Container management
    - Transportation lifecycle
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus, 
                 batch_service, compliance_service, agronomy_service, manifest_service):
        from database.repository import BaseRepository
        from domain.logistics.repositories.load_repository import LoadRepository
        from domain.logistics.entities.vehicle import Vehicle
        from domain.logistics.entities.driver import Driver
        from domain.logistics.entities.contractor import Contractor
        from domain.logistics.entities.container import Container
        from domain.logistics.services.dispatch_service import LogisticsDomainService
        from domain.shared.generic_crud_service import GenericCrudService
        
        # Repositories
        self.load_repository = LoadRepository(db_manager)
        self.vehicle_repository = BaseRepository(db_manager, Vehicle, "vehicles")
        self.driver_repository = BaseRepository(db_manager, Driver, "drivers")
        self.contractor_repository = BaseRepository(db_manager, Contractor, "contractors")
        self.container_repository = BaseRepository(db_manager, Container, "containers")
        
        # Domain Services
        self.dispatch_service = LogisticsDomainService(
            db_manager,
            batch_service,
            compliance_service,
            agronomy_service,
            manifest_service,
            event_bus=event_bus
        )
        
        # Master CRUD Services
        self.vehicle_service = GenericCrudService(self.vehicle_repository)
        self.driver_service = GenericCrudService(self.driver_repository)
        self.contractor_service = GenericCrudService(self.contractor_repository)
        self.container_service = GenericCrudService(self.container_repository)


class AgronomyContainer:
    """
    Container for Agronomy/Disposal bounded context.
    
    Responsibilities:
    - Site and plot management
    - Nitrogen application tracking
    - Site event recording (preparation, closure)
    - Field operations
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus, compliance_service):
        from database.repository import BaseRepository
        from domain.shared.entities.location import Site, Plot
        from domain.disposal.entities.site_event import SiteEvent
        from domain.disposal.entities.application import NitrogenApplication
        from domain.disposal.services.location_service import LocationService
        from domain.disposal.services.agronomy_service import AgronomyDomainService
        from domain.disposal.services.disposal_master_service import DisposalService
        from domain.agronomy.services.machinery_service import MachineryService
        from domain.agronomy.repositories.machine_log_repository import MachineLogRepository
        from domain.agronomy.services.field_reception_handler import FieldReceptionHandler
        
        # Repositories
        self.site_repository = BaseRepository(db_manager, Site, "sites")
        self.plot_repository = BaseRepository(db_manager, Plot, "plots")
        self.site_event_repository = BaseRepository(db_manager, SiteEvent, "site_events")
        self.application_repository = BaseRepository(db_manager, NitrogenApplication, "nitrogen_applications")
        self.machine_log_repository = MachineLogRepository(db_manager)
        
        # Domain Services
        self.location_service = LocationService(self.site_repository, self.plot_repository)
        self.agronomy_service = AgronomyDomainService(db_manager, compliance_service)
        self.disposal_service = DisposalService(db_manager)
        self.machinery_service = MachineryService(db_manager, event_bus)
        self.field_reception_handler = FieldReceptionHandler(db_manager)
        
        # Event subscriptions
        from services.common.event_bus import EventTypes
        event_bus.subscribe(EventTypes.LOAD_ARRIVED_AT_FIELD, 
                          self.field_reception_handler.handle_load_arrived_at_field)


class ProcessingContainer:
    """
    Container for Processing/Treatment bounded context.
    
    Responsibilities:
    - Treatment plant operations
    - Batch management
    - Facility management
    - Quality control (pH, humidity)
    """
    
    def __init__(self, db_manager: DatabaseManager, compliance_service):
        from database.repository import BaseRepository
        from domain.processing.repositories.batch_repository import BatchRepository
        from domain.processing.entities.treatment_plant import TreatmentPlant
        from domain.processing.entities.facility import Facility
        from domain.processing.services.batch_service import TreatmentBatchService
        from domain.processing.services.reception_service import TreatmentReceptionService
        from domain.processing.services.treatment_master_service import TreatmentService
        from domain.shared.generic_crud_service import GenericCrudService
        
        # Repositories
        self.batch_repository = BatchRepository(db_manager)
        self.facility_repository = BaseRepository(db_manager, Facility, "facilities")
        self.treatment_plant_repository = BaseRepository(db_manager, TreatmentPlant, "facilities")
        
        # Domain Services
        self.batch_service = TreatmentBatchService(db_manager)
        self.reception_service = TreatmentReceptionService(db_manager)
        self.treatment_service = TreatmentService(db_manager)
        
        # Master CRUD Services
        self.facility_service = GenericCrudService(self.facility_repository)
        self.treatment_plant_service = GenericCrudService(self.treatment_plant_repository)


class ComplianceContainer:
    """
    Container for Compliance bounded context.
    
    Responsibilities:
    - Regulatory validation
    - Nitrogen capacity tracking
    - Class restrictions
    - Compliance reporting
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus,
                 site_repo, load_repo, batch_repo, application_repo):
        from domain.shared.services.compliance_service import ComplianceService
        from domain.compliance.services.compliance_listener import ComplianceListener
        from services.common.event_bus import EventTypes
        
        # Domain Services
        self.compliance_service = ComplianceService(
            site_repo, load_repo, batch_repo, application_repo
        )
        
        # Listeners
        self.compliance_listener = ComplianceListener(db_manager)
        
        # Event subscriptions
        event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, 
                          self.compliance_listener.handle_load_completed)


class ReportingContainer:
    """
    Container for Reporting bounded context.
    
    Responsibilities:
    - Report generation
    - Dashboard data aggregation
    - Manifest creation
    - Analytics
    """
    
    def __init__(self, db_manager: DatabaseManager, batch_service, compliance_service):
        from repositories.reporting_repository import ReportingRepository
        from services.reporting.reporting_service import ReportingService
        from services.operations.dashboard_service import DashboardService
        from services.operations.manifest_service import ManifestService
        
        # Repositories
        self.reporting_repository = ReportingRepository(db_manager)
        
        # Application Services
        self.reporting_service = ReportingService(self.reporting_repository)
        self.dashboard_service = DashboardService(db_manager)
        self.manifest_service = ManifestService(db_manager, batch_service, compliance_service)


class MastersContainer:
    """
    Container for Master Data bounded context.
    
    Responsibilities:
    - Client management
    - User management
    - Generic CRUD operations for reference data
    """
    
    def __init__(self, db_manager: DatabaseManager):
        from database.repository import BaseRepository
        from domain.shared.entities.client import Client
        from domain.shared.entities.user import User
        from domain.shared.services.auth_service import AuthService
        from domain.shared.generic_crud_service import GenericCrudService
        
        # Repositories
        self.client_repository = BaseRepository(db_manager, Client, "clients")
        self.user_repository = BaseRepository(db_manager, User, "users")
        
        # Services
        self.client_service = GenericCrudService(self.client_repository)
        self.auth_service = AuthService(self.user_repository)


class SatelliteContainer:
    """
    Container for Satellite/Cross-cutting modules.
    
    Responsibilities:
    - Maintenance tracking
    - Finance/costing
    - Event listeners for cross-domain coordination
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: EventBus):
        from domain.maintenance.services.maintenance_listener import MaintenanceListener
        from domain.finance.services.costing_listener import CostingListener
        from services.common.event_bus import EventTypes
        
        # Listeners
        self.maintenance_listener = MaintenanceListener(db_manager)
        self.costing_listener = CostingListener(db_manager)
        
        # Event subscriptions
        event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, 
                          self.maintenance_listener.handle_load_completed)
        event_bus.subscribe(EventTypes.MACHINE_WORK_RECORDED, 
                          self.maintenance_listener.handle_machine_work)
        event_bus.subscribe(EventTypes.LOAD_STATUS_CHANGED, 
                          self.costing_listener.handle_load_completed)
        event_bus.subscribe(EventTypes.MACHINE_WORK_RECORDED, 
                          self.costing_listener.handle_machine_work)


class UIContainer:
    """
    Container for UI-specific services.
    
    Responsibilities:
    - Task resolution for inbox
    - UI state management
    - View orchestration
    """
    
    def __init__(self, load_repo, machine_log_repo):
        from services.ui.task_resolver import TaskResolver
        
        self.task_resolver = TaskResolver(load_repo, machine_log_repo)


@st.cache_resource
def get_container() -> SimpleNamespace:
    """
    Creates and returns a modular dependency injection container.
    
    The container is organized by bounded contexts, making dependencies
    easier to understand and maintain. Each sub-container handles a
    specific domain area.
    
    Returns:
        SimpleNamespace with the following structure:
            - db_manager: DatabaseManager instance
            - event_bus: EventBus instance
            - logistics: LogisticsContainer
            - agronomy: AgronomyContainer
            - processing: ProcessingContainer
            - compliance: ComplianceContainer
            - reporting: ReportingContainer
            - masters: MastersContainer
            - satellite: SatelliteContainer
            - ui: UIContainer
            
            Plus backward compatibility aliases for existing code.
            
    Example:
        >>> container = get_container()
        >>> container.logistics.dispatch_service.create_request(...)
        >>> container.agronomy.location_service.get_all_sites()
        >>> container.reporting.dashboard_service.get_metrics()
    """
    # Core infrastructure
    db_manager = DatabaseManager()
    event_bus = EventBus()
    
    # Initialize Processing first (needed by others)
    processing = ProcessingContainer(db_manager, None)  # Will set compliance later
    
    # Initialize Compliance (needs repositories from other contexts)
    from database.repository import BaseRepository
    from domain.shared.entities.location import Site
    from domain.disposal.entities.application import NitrogenApplication
    
    site_repo = BaseRepository(db_manager, Site, "sites")
    application_repo = BaseRepository(db_manager, NitrogenApplication, "nitrogen_applications")
    
    compliance = ComplianceContainer(
        db_manager, 
        event_bus,
        site_repo,
        None,  # Will get load_repo from logistics
        processing.batch_repository,
        application_repo
    )
    
    # Initialize Agronomy
    agronomy = AgronomyContainer(db_manager, event_bus, compliance.compliance_service)
    
    # Initialize Reporting
    reporting = ReportingContainer(
        db_manager, 
        processing.batch_service, 
        compliance.compliance_service
    )
    
    # Initialize Logistics (depends on most other services)
    logistics = LogisticsContainer(
        db_manager,
        event_bus,
        processing.batch_service,
        compliance.compliance_service,
        agronomy.agronomy_service,
        reporting.manifest_service
    )
    
    # Update compliance with load_repo
    compliance.compliance_service.load_repo = logistics.load_repository
    
    # Initialize Masters
    masters = MastersContainer(db_manager)
    
    # Initialize Satellite modules
    satellite = SatelliteContainer(db_manager, event_bus)
    
    # Initialize UI
    ui = UIContainer(logistics.load_repository, agronomy.machine_log_repository)
    
    # Create container with bounded contexts
    container = SimpleNamespace(
        # Core infrastructure
        db_manager=db_manager,
        event_bus=event_bus,
        
        # Bounded contexts
        logistics=logistics,
        agronomy=agronomy,
        processing=processing,
        compliance=compliance,
        reporting=reporting,
        masters=masters,
        satellite=satellite,
        ui=ui,
    )
    
    # Add backward compatibility aliases (to avoid breaking existing UI code)
    _add_backward_compatibility_aliases(container)
    
    return container


def _add_backward_compatibility_aliases(container: SimpleNamespace) -> None:
    """
    Adds backward compatibility aliases to the container.
    
    This allows existing UI code to continue working while we gradually
    migrate to the new structured approach.
    
    TODO: Remove these aliases after UI migration is complete.
    """
    # Logistics aliases
    container.dispatch_service = container.logistics.dispatch_service
    container.reception_service = container.logistics.dispatch_service
    container.logistics_service = container.logistics.dispatch_service
    container.vehicle_service = container.logistics.vehicle_service
    container.driver_service = container.logistics.driver_service
    container.contractor_service = container.logistics.contractor_service
    container.container_service = container.logistics.container_service
    
    # Agronomy aliases
    container.location_service = container.agronomy.location_service
    container.disposal_service = container.agronomy.agronomy_service
    container.agronomy_service = container.agronomy.agronomy_service
    container.site_prep_service = container.agronomy.agronomy_service
    container.nitrogen_app_service = container.agronomy.agronomy_service
    container.machinery_service = container.agronomy.machinery_service
    container.master_disposal_service = container.agronomy.disposal_service
    
    # Processing aliases
    container.batch_service = container.processing.batch_service
    container.treatment_batch_service = container.processing.batch_service
    container.treatment_reception_service = container.processing.reception_service
    container.facility_service = container.processing.facility_service
    container.treatment_plant_service = container.processing.treatment_plant_service
    container.treatment_service = container.processing.treatment_service
    
    # Compliance aliases
    container.compliance_service = container.compliance.compliance_service
    
    # Reporting aliases
    container.reporting_service = container.reporting.reporting_service
    container.dashboard_service = container.reporting.dashboard_service
    container.manifest_service = container.reporting.manifest_service
    
    # Masters aliases
    container.client_service = container.masters.client_service
    container.auth_service = container.masters.auth_service
    
    # UI aliases
    container.task_resolver = container.ui.task_resolver

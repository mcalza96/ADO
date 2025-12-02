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
from repositories.load_repository import LoadRepository
from repositories.batch_repository import BatchRepository
from repositories.reporting_repository import ReportingRepository
from database.repository import BaseRepository

# Models for Generic Repositories
from models.masters.location import Site, Plot
from models.operations.site_event import SiteEvent
from models.auth.user import User
from models.agronomy.application import NitrogenApplication
from models.masters.client import Client
from models.masters.transport import Contractor
from models.masters.driver import Driver
from models.masters.vehicle import Vehicle
from models.masters.treatment_plant import TreatmentPlant
from models.masters.container import Container

from services.masters.location_service import LocationService
from services.operations.logistics_domain_service import LogisticsDomainService
from services.operations.agronomy_domain_service import AgronomyDomainService
from services.auth_service import AuthService
from services.operations.manifest_service import ManifestService
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from services.operations.treatment_reception import TreatmentReceptionService
from services.operations.treatment_batch_service import TreatmentBatchService
from services.generic_crud_service import GenericCrudService
from services.masters.disposal_service import DisposalService as MasterDisposalService
from services.masters.treatment_service import TreatmentService
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
    # Initialize Repositories
    # Generic Repositories
    site_repo = BaseRepository(db_manager, Site, "sites")
    plot_repo = BaseRepository(db_manager, Plot, "plots")
    site_event_repo = BaseRepository(db_manager, SiteEvent, "site_events")
    user_repo = BaseRepository(db_manager, User, "users")
    application_repo = BaseRepository(db_manager, NitrogenApplication, "nitrogen_applications")
    vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
    client_repo = BaseRepository(db_manager, Client, "clients")
    contractor_repo = BaseRepository(db_manager, Contractor, "contractors")
    driver_repo = BaseRepository(db_manager, Driver, "drivers")
    
    # Specific Repositories (Custom SQL or Logic)
    load_repo = LoadRepository(db_manager)
    batch_repo = BatchRepository(db_manager)
    reporting_repo = ReportingRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(site_repo, plot_repo)
    batch_service = BatchService(db_manager)
    
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
        manifest_service
    )
    
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
    
    # Master Services
    client_service = GenericCrudService(client_repo)
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
        reporting_service=reporting_service,
        agronomy_service=agronomy_service,
    )

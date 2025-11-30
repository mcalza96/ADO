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
from repositories.vehicle_repository import VehicleRepository

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
    load_repo = LoadRepository(db_manager)
    site_event_repo = SiteEventRepository(db_manager)
    user_repo = UserRepository(db_manager)
    batch_repo = BatchRepository(db_manager)
    application_repo = ApplicationRepository(db_manager)
    vehicle_repo = VehicleRepository(db_manager)
    
    # Initialize Services with dependency injection
    location_service = LocationService(db_manager)
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
        batch_service=batch_service
    )

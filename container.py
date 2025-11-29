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
from services.masters.location_service import LocationService
from services.operations.disposal_execution import DisposalExecutionService
from services.auth_service import AuthService


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
    
    # Initialize Services with dependency injection
    location_service = LocationService(db_manager)
    disposal_service = DisposalExecutionService(db_manager)
    auth_service = AuthService(user_repo)
    
    # Return a simple container object with services as attributes
    return SimpleNamespace(
        db_manager=db_manager,
        location_service=location_service,
        disposal_service=disposal_service,
        auth_service=auth_service
    )

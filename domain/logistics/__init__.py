"""
Logistics Domain - Gestión de transporte y despacho de biosólidos.

Este dominio maneja:
- Cargas (Load) y sus estados
- Transiciones de estado con validaciones
- Contenedores y vehículos
- Solicitudes de retiro (Pickup Requests)
"""

from .entities import (
    Load,
    LoadStatus,
    Container,
    ContainerStatus,
    Contractor,
    Driver,
    Vehicle,
    VehicleType,
    PickupRequest,
    PickupRequestStatus,
    StatusTransition,
)
from .services import (
    LogisticsDomainService,
    PickupRequestService,
    is_valid_transition,
)
from .repositories import (
    LoadRepository,
    StatusTransitionRepository,
)

__all__ = [
    # Entities
    'Load',
    'LoadStatus',
    'Container',
    'ContainerStatus',
    'Contractor',
    'Driver',
    'Vehicle',
    'VehicleType',
    'PickupRequest',
    'PickupRequestStatus',
    'StatusTransition',
    # Services
    'LogisticsDomainService',
    'PickupRequestService',
    'is_valid_transition',
    # Repositories
    'LoadRepository',
    'StatusTransitionRepository',
]
"""Logistics Domain Entities."""

from .load import Load
from .load_status import LoadStatus, normalize_status
from .container import Container, ContainerStatus
from .container_filling_record import ContainerFillingRecord, ContainerFillingStatus
from .contractor import Contractor
from .driver import Driver
from .vehicle import Vehicle, VehicleType, AssetType
from .pickup_request import PickupRequest, PickupRequestStatus
from .status_transition import StatusTransition

__all__ = [
    'Load',
    'LoadStatus',
    'normalize_status',
    'Container',
    'ContainerStatus',
    'ContainerFillingRecord',
    'ContainerFillingStatus',
    'Contractor',
    'Driver',
    'Vehicle',
    'VehicleType',
    'AssetType',
    'PickupRequest',
    'PickupRequestStatus',
    'StatusTransition',
]
"""
UI Masters Module - Gestión de datos maestros

Este módulo contiene las vistas para la gestión de datos maestros del sistema:
- containers_view: Gestión de contenedores (tolvas)
- locations_view: Gestión de predios y parcelas
- security_view: Gestión de usuarios y seguridad
- transport_view: Gestión de transporte (contratistas, choferes, vehículos)
"""

from . import containers_view
from . import locations_view
from . import security_view
from . import transport_view

__all__ = [
    'containers_view',
    'locations_view',
    'security_view',
    'transport_view'
]

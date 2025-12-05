"""
Logistics Module Registration - Registro de páginas de logística.

Este módulo registra las vistas de logística en el UIRegistry.
Las implementaciones están en ui/logistics/ (módulos separados).

IMPORTANTE: Para planificación, usar ui/planning_view.py que es la
versión refactorizada con Presenters y componentes reutilizables.

Al importar este módulo, las páginas se registran automáticamente
en el UIRegistry, permitiendo su uso dinámico en main.py.
"""

from ui.registry import UIRegistry, MenuItem

# Importar vistas refactorizadas desde el nuevo módulo de logística
from ui.logistics.dispatch_view import dispatch_page
from ui.logistics.field_reception_view import field_reception_page
from ui.logistics.tracking_view import tracking_page

# Para planificación, usar la vista refactorizada con Presenter
from ui.planning_view import planning_page


def _planning_page_wrapper(container):
    """
    Wrapper para planning_page que adapta la firma del contenedor.
    
    planning_page espera servicios individuales, pero el registry
    pasa el container completo.
    """
    planning_page(
        logistics_service=container.logistics_service,
        contractor_service=container.contractor_service,
        driver_service=container.driver_service,
        vehicle_service=container.vehicle_service,
        location_service=container.location_service,
        treatment_plant_service=container.treatment_plant_service
    )


# ============================================================================
# MODULE REGISTRATION
# ============================================================================

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Planificación",
        icon="📋",
        page_func=_planning_page_wrapper,
        permission_required="planning",
        order=5,
        description="Planificar transportes",
        visible_for_roles=["Admin", "Planificador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Despacho",
        icon="🚛",
        page_func=dispatch_page,
        permission_required="dispatch",
        order=10,
        description="Despachar cargas hacia predios",
        visible_for_roles=["Admin", "Operador", "Planificador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Recepción en Campo",
        icon="📦",
        page_func=field_reception_page,
        permission_required="reception",
        order=20,
        description="Registrar llegada de cargas",
        visible_for_roles=["Admin", "Operador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Seguimiento",
        icon="📍",
        page_func=tracking_page,
        permission_required="tracking",
        order=30,
        description="Rastrear cargas en tiempo real",
        visible_for_roles=None  # Visible para todos
    )
)

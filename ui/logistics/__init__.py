"""
Logistics UI Module.

Este módulo contiene las vistas refactorizadas de logística,
separadas en archivos enfocados siguiendo el Single Responsibility Principle.

Estructura:
- dispatch_view.py: Despacho de camiones
- field_reception_view.py: Recepción en campo  
- tracking_view.py: Seguimiento en tiempo real
- pickup_requests_view.py: Solicitudes de retiro de clientes

Nota: planning_page ahora se encuentra en ui/planning_view.py
que es la versión refactorizada y preferida.
"""

from ui.logistics.dispatch_view import dispatch_page
from ui.logistics.field_reception_view import field_reception_page
from ui.logistics.tracking_view import tracking_page
from ui.logistics.pickup_requests_view import pickup_requests_page

__all__ = [
    'dispatch_page',
    'field_reception_page', 
    'tracking_page',
    'pickup_requests_page'
]

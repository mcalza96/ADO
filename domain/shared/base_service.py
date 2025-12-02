from typing import List, Optional, Type, TypeVar, Any
"""
Base Service class for all domain services.

Provides common infrastructure for services including access to the database
and event bus for inter-service communication.
"""

from database.db_manager import DatabaseManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.common.event_bus import EventBus


class BaseService:
    """
    Clase base para todos los servicios del dominio.
    
    Proporciona acceso centralizado al DatabaseManager y al EventBus.
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: 'EventBus' = None):
        """
        Inicializa el servicio base.
        
        Args:
            db_manager: Gestor de base de datos
            event_bus: Bus de eventos para comunicación entre servicios (opcional)
        """
        self.db_manager = db_manager
        self._event_bus = event_bus
    
    @property
    def event_bus(self) -> 'EventBus':
        """
        Acceso al bus de eventos.
        
        Returns:
            EventBus: Instancia del bus de eventos o None si no está configurado
        """
        return self._event_bus

    # Methods execute_query and execute_non_query have been removed to enforce Repository Pattern usage.

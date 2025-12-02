"""
Event Bus - Sistema de eventos simple y sincrónico para desacoplar servicios.

Este módulo implementa un patrón de publicación/suscripción (pub/sub) que permite
que los servicios publiquen eventos y otros servicios se suscriban a ellos sin
acoplamiento directo.

Ejemplo de uso:
    >>> bus = EventBus()
    >>> bus.subscribe('LoadDelivered', lambda event: print(f"Load {event.data['load_id']} delivered"))
    >>> bus.publish(Event('LoadDelivered', {'load_id': 123}))
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """
    Representa un evento en el sistema.
    
    Attributes:
        event_type: Tipo de evento (ej: 'LoadDelivered', 'BatchCreated')
        data: Datos asociados al evento
        timestamp: Momento en que se creó el evento
    """
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """
    Bus de eventos sincrónico simple para desacoplar servicios.
    
    Permite que los servicios publiquen eventos y se suscriban a ellos
    sin conocer la implementación de otros servicios.
    """
    
    def __init__(self):
        """Inicializa el bus de eventos con un diccionario vacío de suscriptores."""
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Suscribe un manejador a un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento al que suscribirse (ej: 'LoadDelivered')
            handler: Función que se ejecutará cuando se publique el evento.
                     Debe aceptar un parámetro Event.
        
        Example:
            >>> def on_load_delivered(event: Event):
            ...     print(f"Load {event.data['load_id']} delivered")
            >>> bus.subscribe('LoadDelivered', on_load_delivered)
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: Event) -> None:
        """
        Publica un evento, ejecutando todos los manejadores suscritos.
        
        Args:
            event: Evento a publicar
        
        Note:
            La ejecución es sincrónica: cada manejador se ejecuta
            secuencialmente antes de que publish() retorne.
        
        Example:
            >>> bus.publish(Event('LoadDelivered', {'load_id': 123, 'destination': 'Plant A'}))
        """
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log el error pero continúa ejecutando otros handlers
                    print(f"⚠️  Error in event handler for {event.event_type}: {e}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Desuscribe un manejador de un tipo de evento.
        
        Args:
            event_type: Tipo de evento
            handler: Manejador a desuscribir
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass  # Handler no estaba suscrito
    
    def clear(self, event_type: str = None) -> None:
        """
        Elimina todos los suscriptores de un tipo de evento o de todos los eventos.
        
        Args:
            event_type: Tipo de evento a limpiar. Si es None, limpia todos.
        """
        if event_type is None:
            self._subscribers.clear()
        elif event_type in self._subscribers:
            del self._subscribers[event_type]


# Tipos de eventos del dominio
class EventTypes:
    """Constantes para los tipos de eventos del sistema."""
    
    # Logistics
    LOAD_CREATED = 'LoadCreated'
    LOAD_ACCEPTED = 'LoadAccepted'
    LOAD_IN_TRANSIT = 'LoadInTransit'
    LOAD_ARRIVED = 'LoadArrived'
    LOAD_DELIVERED = 'LoadDelivered'
    LOAD_STATUS_CHANGED = 'LoadStatusChanged'  # Nuevo: Genérico para cualquier cambio de estado
    LOAD_ARRIVED_AT_FIELD = 'LoadArrivedAtField'  # Nuevo: Específico para llegada a campo
    
    # Processing
    BATCH_CREATED = 'BatchCreated'
    BATCH_READY = 'BatchReady'
    BATCH_DISPATCHED = 'BatchDispatched'
    
    # Disposal
    APPLICATION_STARTED = 'ApplicationStarted'
    APPLICATION_COMPLETED = 'ApplicationCompleted'
    SITE_PREPARED = 'SitePrepared'
    
    # Machinery (Nuevo)
    MACHINE_WORK_RECORDED = 'MachineWorkRecorded'


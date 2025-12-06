from infrastructure.events.event_bus import Event
from infrastructure.persistence.database_manager import DatabaseManager
from datetime import datetime


class FieldReceptionHandler:
    """
    Maneja el evento de llegada de carga al campo.
    
    Crea automáticamente un borrador de ApplicationBatch para facilitar
    el registro de la aplicación agronómica.
    
    Este handler conecta el dominio de Logística con el de Agronomía,
    permitiendo que el flujo de trabajo continúe sin intervención manual.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def handle_load_arrived_at_field(self, event: Event) -> None:
        """
        Procesa evento LoadArrivedAtField.
        
        Crea ApplicationBatch en estado DRAFT vinculado a la carga.
        
        Args:
            event: Evento con data={'load_id': int, 'site_id': int, 'timestamp': str}
        
        Example:
            >>> handler = FieldReceptionHandler(db_manager)
            >>> event = Event('LoadArrivedAtField', {'load_id': 123, 'site_id': 5})
            >>> handler.handle_load_arrived_at_field(event)
            📍 Carga 123 llegó al campo (sitio 5)
               Preparar para crear ApplicationBatch en estado DRAFT
        """
        load_id = event.data['load_id']
        site_id = event.data['site_id']
        timestamp = event.data.get('timestamp', datetime.now().isoformat())
        
        # TODO: Implementar creación de ApplicationBatch
        # Por ahora, solo registrar el evento para verificación
        print(f"📍 Carga {load_id} llegó al campo (sitio {site_id}) a las {timestamp}")
        print(f"   Preparar para crear ApplicationBatch en estado DRAFT")
        print(f"   [PENDIENTE: Implementar creación automática de ApplicationBatch]")

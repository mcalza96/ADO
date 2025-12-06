from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from infrastructure.persistence.database_manager import DatabaseManager
from domain.agronomy.repositories.machine_log_repository import MachineLogRepository
from domain.agronomy.entities.machine_log import MachineLog
from domain.shared.exceptions import DomainException
from infrastructure.events.event_bus import EventBus, Event, EventTypes


class MachineryService:
    """
    Servicio para gestión de maquinaria pesada y registro de trabajo.
    
    Implementa validaciones críticas:
    - Consistencia de horómetros (end > start)
    - Continuidad entre registros (previene fraude)
    
    Publica eventos para integración con mantenimiento.
    """
    
    def __init__(self, db_manager: DatabaseManager, event_bus: Optional[EventBus] = None):
        self.db_manager = db_manager
        self.log_repo = MachineLogRepository(db_manager)
        self.event_bus = event_bus
    
    def register_log(self, data: Dict[str, Any]) -> MachineLog:
        """
        Registra un log de trabajo de maquinaria con validaciones.
        
        Validaciones:
        1. end_hourmeter > start_hourmeter (consistencia básica)
        2. start_hourmeter >= último end_hourmeter (continuidad)
        
        Args:
            data: Diccionario con datos del log:
                - machine_id (int): ID de la máquina
                - operator_id (int): ID del operador
                - site_id (int): ID del sitio
                - start_hourmeter (float): Horómetro inicial
                - end_hourmeter (float): Horómetro final
                - date (datetime, optional): Fecha del trabajo
                - activities (list, optional): Lista de actividades
                - created_by_user_id (int, optional): Usuario que registra
        
        Returns:
            MachineLog: Log creado y guardado
            
        Raises:
            DomainException: Si falla alguna validación
            
        Example:
            >>> log = service.register_log({
            ...     'machine_id': 5,
            ...     'operator_id': 10,
            ...     'site_id': 3,
            ...     'start_hourmeter': 1000.0,
            ...     'end_hourmeter': 1008.5,
            ...     'activities': [{'task': 'Excavación', 'plot_id': 7}]
            ... })
            >>> print(log.total_hours)  # Decimal('8.5')
        """
        machine_id = data['machine_id']
        start_hm = Decimal(str(data['start_hourmeter']))
        end_hm = Decimal(str(data['end_hourmeter']))
        
        # Validación 1: Consistencia básica
        if end_hm <= start_hm:
            raise DomainException(
                f"Horómetro final ({end_hm}) debe ser mayor al inicial ({start_hm})"
            )
        
        # Validación 2: Continuidad con registro anterior
        latest_log = self.log_repo.get_latest_log_by_machine(machine_id)
        if latest_log:
            if start_hm < latest_log.end_hourmeter:
                raise DomainException(
                    f"Horómetro inicial ({start_hm}) no puede ser menor "
                    f"al horómetro final del registro anterior ({latest_log.end_hourmeter}). "
                    f"Esto puede indicar un error de captura o intento de fraude."
                )
        
        # Crear log
        log = MachineLog(
            id=None,
            machine_id=machine_id,
            date=data.get('date', datetime.now()),
            operator_id=data['operator_id'],
            site_id=data['site_id'],
            start_hourmeter=start_hm,
            end_hourmeter=end_hm,
            activities=data.get('activities', []),
            created_at=datetime.now(),
            created_by_user_id=data.get('created_by_user_id')
        )
        
        # Guardar
        saved_log = self.log_repo.add(log)
        
        # Publicar evento
        if self.event_bus:
            self.event_bus.publish(Event(
                event_type=EventTypes.MACHINE_WORK_RECORDED,
                data={
                    'log_id': saved_log.id,
                    'machine_id': machine_id,
                    'total_hours': float(saved_log.total_hours),
                    'site_id': saved_log.site_id,
                    'date': saved_log.date.isoformat()
                }
            ))
        
        return saved_log
    
    def get_machine_logs(self, machine_id: int) -> list[MachineLog]:
        """
        Obtiene el historial de trabajo de una máquina.
        
        Args:
            machine_id: ID de la máquina
            
        Returns:
            Lista de logs ordenados por fecha descendente
        """
        return self.log_repo.get_by_machine_id(machine_id)
    
    def get_site_logs(self, site_id: int) -> list[MachineLog]:
        """
        Obtiene todos los registros de trabajo en un sitio.
        
        Args:
            site_id: ID del sitio
            
        Returns:
            Lista de logs ordenados por fecha descendente
        """
        return self.log_repo.get_by_site_id(site_id)

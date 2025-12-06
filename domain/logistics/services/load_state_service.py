"""
LoadStateService - Maneja transiciones de estado y atributos JSONB.

Responsabilidades:
- Ejecutar transiciones de estado con validación FSM
- Gestionar atributos JSONB (checkpoints)
- Promover datos críticos de JSON a columnas SQL
- Registrar historial de transiciones
- Publicar eventos de cambio de estado
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from infrastructure.persistence.database_manager import DatabaseManager
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.repositories.status_transition_repository import StatusTransitionRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus, normalize_status
from domain.logistics.entities.status_transition import StatusTransition
from domain.logistics.services.transition_rules import (
    get_validators_for_transition,
    is_valid_transition,
)
from domain.shared.exceptions import TransitionException, DomainException
from infrastructure.events.event_bus import EventBus, Event, EventTypes


class LoadStateService:
    """
    Servicio especializado en gestión de estados de carga.
    
    Implementa la máquina de estados finitos (FSM) para el ciclo de vida
    de las cargas, garantizando que todas las transiciones sean válidas
    y cumplan con los verificadores (checkpoints) requeridos.
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        event_bus: Optional[EventBus] = None
    ):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.transition_repo = StatusTransitionRepository(db_manager)
        self.event_bus = event_bus

    def transition_load(
        self,
        load_id: int,
        new_status: LoadStatus,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Transiciona una carga a un nuevo estado, validando verificadores.

        Este método implementa:
        1. Validación de transición válida (FSM)
        2. Ejecución de validadores de checkpoints
        3. Registro de transición en historial
        4. Actualización del estado de la carga
        5. Promoción de atributos JSONB a columnas SQL
        6. Publicación de eventos

        Args:
            load_id: ID de la carga
            new_status: Estado destino (LoadStatus enum)
            user_id: Usuario que realiza la transición
            notes: Notas opcionales sobre la transición

        Returns:
            True si la transición fue exitosa

        Raises:
            ValueError: Si la carga no existe
            TransitionException: Si la transición no es válida desde el estado actual
            DomainException: Si faltan verificadores requeridos

        Example:
            # Transición exitosa con todos los verificadores
            load.attributes = {
                'entry_weight_ticket': 'TKT-001',
                'lab_analysis_result': {'ph': 7.2},
                'exit_weight_ticket': 'TKT-002'
            }
            service.transition_load(load_id, LoadStatus.COMPLETED, user_id=5)
        """
        # 1. Obtener carga actual
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")

        # Convertir estado actual a LoadStatus si es string legacy
        try:
            current_status = LoadStatus(load.status)
        except ValueError:
            # Intentar mapeo legacy
            current_status = normalize_status(load.status)

        # 2. Validar que la transición sea permitida (FSM)
        if not is_valid_transition(current_status, new_status):
            raise TransitionException(
                f"Transición inválida: {current_status.value} -> {new_status.value}. "
                f"Esta transición no está permitida por las reglas de negocio."
            )

        # 3. Determinar si es flujo de disposición
        is_disposal_flow = load.destination_site_id is not None

        # 4. Ejecutar validadores de verificadores (checkpoints)
        validators = get_validators_for_transition(
            to_status=new_status,
            from_status=current_status,
            is_disposal_flow=is_disposal_flow
        )

        # Asegurar que attributes existe
        if not hasattr(load, 'attributes') or load.attributes is None:
            load.attributes = {}

        for validator in validators:
            try:
                validator(load.attributes)
            except DomainException as e:
                # Re-lanzar con contexto adicional
                raise DomainException(
                    f"No se puede transicionar a {new_status.value}: {str(e)}"
                )

        # 5. Registrar transición en historial
        transition = StatusTransition(
            id=None,
            load_id=load_id,
            from_status=current_status.value,
            to_status=new_status.value,
            timestamp=datetime.now(),
            user_id=user_id,
            notes=notes
        )
        self.transition_repo.add(transition)

        # 6. Actualizar estado de la carga
        load.status = new_status.value
        load.updated_at = datetime.now()

        # 7. Promoción de atributos JSONB a columnas SQL (para BI/Reporting)
        self._promote_attributes_to_columns(load)

        success = self.load_repo.update(load)
        
        # 8. Publicar eventos
        if success and self.event_bus:
            self._publish_status_change_events(
                load_id=load_id,
                current_status=current_status,
                new_status=new_status,
                load=load,
                user_id=user_id
            )
        
        return success

    def _promote_attributes_to_columns(self, load: Load) -> None:
        """
        Promociona datos críticos de JSONB attributes a columnas SQL.
        
        Esto facilita el análisis BI y reportes sin parsear JSON.
        """
        # Promoción de pesos
        if 'gross_weight' in load.attributes:
            try:
                load.gross_weight = float(load.attributes['gross_weight'])
            except (ValueError, TypeError):
                pass  # Mantener valor original o None
        
        if 'tare_weight' in load.attributes:
            try:
                load.tare_weight = float(load.attributes['tare_weight'])
            except (ValueError, TypeError):
                pass

        # Calcular peso neto si ambos pesos están disponibles
        if load.gross_weight is not None and load.tare_weight is not None:
            load.net_weight = load.gross_weight - load.tare_weight
            load.weight_net = load.net_weight  # Alias

    def _publish_status_change_events(
        self,
        load_id: int,
        current_status: LoadStatus,
        new_status: LoadStatus,
        load: Load,
        user_id: Optional[int]
    ) -> None:
        """Publica eventos relacionados con cambios de estado."""
        # Evento principal: cambio de estado
        self.event_bus.publish(Event(
            event_type=EventTypes.LOAD_STATUS_CHANGED,
            data={
                'load_id': load_id,
                'from_status': current_status.value,
                'to_status': new_status.value,
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id
            }
        ))
        
        # Evento especial: llegada a campo de aplicación
        if new_status == LoadStatus.AT_DESTINATION and load.destination_site_id:
            self.event_bus.publish(Event(
                event_type=EventTypes.LOAD_ARRIVED_AT_FIELD,
                data={
                    'load_id': load_id,
                    'site_id': load.destination_site_id,
                    'timestamp': datetime.now().isoformat()
                }
            ))

    def update_load_attributes(
        self,
        load_id: int,
        attributes_dict: Dict[str, Any]
    ) -> bool:
        """
        Actualiza los atributos JSONB de una carga sin cambiar su estado.
        
        Método útil para guardar datos de formularios (checkpoints) antes de
        intentar una transición de estado. Los atributos se mergean con los existentes.
        
        Args:
            load_id: ID de la carga
            attributes_dict: Diccionario con atributos a agregar/actualizar
            
        Returns:
            True si la actualización fue exitosa
            
        Raises:
            ValueError: Si la carga no existe
            
        Example:
            # Guardar resultado de análisis de laboratorio
            service.update_load_attributes(load_id, {
                'lab_analysis_result': {
                    'ph': 7.2,
                    'humidity': 75.5,
                    'timestamp': '2024-12-02T10:30:00'
                }
            })
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
        
        # Asegurar que attributes existe
        if not hasattr(load, 'attributes') or load.attributes is None:
            load.attributes = {}
        
        # Mergear nuevos atributos
        load.attributes.update(attributes_dict)
        
        # Actualizar timestamps de sincronización
        load.updated_at = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def get_load_timeline(self, load_id: int) -> List[StatusTransition]:
        """
        Obtiene el historial completo de estados de una carga.

        Args:
            load_id: ID de la carga

        Returns:
            Lista de transiciones ordenadas cronológicamente

        Example:
            timeline = service.get_load_timeline(123)
            for transition in timeline:
                print(f"{transition.timestamp}: {transition.from_status} -> {transition.to_status}")
        """
        return self.transition_repo.get_by_load_id(load_id)

    def get_time_in_status(
        self,
        load_id: int,
        status: LoadStatus
    ) -> Optional[timedelta]:
        """
        Calcula el tiempo que una carga estuvo/está en un estado específico.

        Útil para cálculos de SLA y análisis de rendimiento.

        Args:
            load_id: ID de la carga
            status: Estado a medir (LoadStatus enum)

        Returns:
            timedelta con la duración total, o None si nunca estuvo en ese estado

        Example:
            duration = service.get_time_in_status(123, LoadStatus.AT_DESTINATION)
            if duration:
                hours = duration.total_seconds() / 3600
                print(f"La carga estuvo {hours:.1f} horas en destino")
        """
        return self.transition_repo.get_time_in_status(load_id, status.value)

    def get_current_state_duration(self, load_id: int) -> Optional[timedelta]:
        """
        Calcula cuánto tiempo lleva la carga en su estado actual.

        Args:
            load_id: ID de la carga

        Returns:
            timedelta desde la última transición, o None si no hay historial
        """
        latest = self.transition_repo.get_latest_transition(load_id)
        if not latest:
            return None
        return timedelta(seconds=latest.duration_since)

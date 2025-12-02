from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.repositories.status_transition_repository import StatusTransitionRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.status_transition import StatusTransition
from domain.logistics.entities.vehicle import Vehicle
from domain.logistics.entities.container import Container
from domain.logistics.services.transition_rules import (
    get_validators_for_transition,
    is_valid_transition,
)
from domain.processing.services.batch_service import TreatmentBatchService
from domain.shared.services.compliance_service import ComplianceService
from domain.disposal.services.agronomy_service import AgronomyDomainService
from services.operations.manifest_service import ManifestService
from domain.shared.exceptions import TransitionException, ComplianceViolationError, DomainException
from domain.shared.constants import SLUDGE_DENSITY

class LogisticsDomainService:
    """
    Handles the complete Transport Lifecycle:
    Planning -> Dispatch -> Transit -> Reception -> Closing
    
    Consolidates:
    - LogisticsService (Planning)
    - DispatchService (Gate Out)
    - ReceptionService (Gate In)
    """
    def __init__(
        self,
        db_manager: DatabaseManager,
        batch_service: TreatmentBatchService,
        compliance_service: ComplianceService,
        agronomy_service: AgronomyDomainService,
        manifest_service: ManifestService,
        event_bus: 'EventBus' = None  # Nuevo: EventBus para publicar eventos
    ):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.transition_repo = StatusTransitionRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.container_repo = BaseRepository(db_manager, Container, "containers")
        
        self.batch_service = batch_service
        self.treatment_batch_service = TreatmentBatchService(db_manager)
        self.compliance_service = compliance_service
        self.agronomy_service = agronomy_service
        self.manifest_service = manifest_service
        self.event_bus = event_bus  # Nuevo

    # --- Planning Phase ---
    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None) -> Load:
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            origin_treatment_plant_id=plant_id,
            status='Requested',
            requested_date=requested_date,
            created_at=datetime.now()
        )
        return self.load_repo.add(load)

    def schedule_load(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, 
                         site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, 
                         container_quantity: Optional[int] = None) -> bool:
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'Requested':
            raise TransitionException(f"Cannot schedule load. Current status: {load.status}. Expected: 'Requested'.")
        
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.container_quantity = container_quantity
        
        if treatment_plant_id:
            load.destination_treatment_plant_id = treatment_plant_id
            load.destination_site_id = None
        else:
            load.destination_site_id = site_id
            load.destination_treatment_plant_id = None
            
        load.scheduled_date = scheduled_date
        load.status = 'Scheduled'
        load.updated_at = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    # --- Dispatch Phase (Gate Out) ---
    def _validate_capacity(self, vehicle_id: int, container_id: Optional[int]) -> None:
        if not container_id:
            return 
        
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        container = self.container_repo.get_by_id(container_id)
        
        if not vehicle or not container:
            return 
            
        estimated_weight = container.capacity_m3 * SLUDGE_DENSITY
        if estimated_weight > vehicle.capacity_wet_tons:
             raise ValueError(f"Capacity Risk: Container {container.code} ({container.capacity_m3}m3) estimated weight ({estimated_weight:.2f}t) exceeds Vehicle {vehicle.license_plate} capacity ({vehicle.capacity_wet_tons}t).")

    def dispatch_truck(
        self,
        batch_id: int,
        driver_id: int,
        vehicle_id: int,
        destination_site_id: int,
        origin_facility_id: int,
        weight_net: float,
        guide_number: Optional[str] = None,
        container_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dispatches a truck (Sprint 2 / Legacy Flow).
        """
        self._validate_capacity(vehicle_id, container_id)
        
        # Validation
        available = self.batch_service.get_batch_balance(batch_id)
        if weight_net > available:
            raise ValueError(f"Stock insuficiente. Disponible: {available} kg, Solicitado: {weight_net} kg")
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if weight_net > vehicle.max_capacity:
            raise ValueError(f"Peso excede capacidad del vehículo.")
            
        try:
            self.compliance_service.validate_dispatch(batch_id, destination_site_id, weight_net)
        except ComplianceViolationError as e:
            raise ValueError(f"🚫 OPERACIÓN BLOQUEADA: {str(e)}")

        with self.db_manager as conn:
            load = Load(
                id=None,
                origin_facility_id=origin_facility_id,
                destination_site_id=destination_site_id,
                batch_id=batch_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                container_id=container_id,
                weight_net=weight_net,
                guide_number=guide_number,
                status='InTransit',
                dispatch_time=datetime.now(),
                created_at=datetime.now()
            )
            
            created_load = self.load_repo.create_load(load)
            self.treatment_batch_service.reserve_stock(batch_id, weight_net)
            
            # Register Nitrogen
            self.agronomy_service.register_nitrogen_application(
                site_id=destination_site_id,
                load_id=created_load.id,
                batch_id=batch_id,
                weight_net=weight_net
            )
            
            manifest_path = self.manifest_service.generate_manifest(created_load.id)
            
            return {
                "status": "success",
                "load_id": created_load.id,
                "manifest_code": created_load.manifest_code,
                "manifest_path": manifest_path
            }

    def accept_trip(self, load_id: int) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != 'Scheduled':
            raise ValueError("Invalid load or status")
        load.status = 'Accepted'
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    def start_trip(self, load_id: int) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != 'Accepted':
            raise ValueError("Invalid load or status")
        load.status = 'InTransit'
        load.dispatch_time = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    # --- Reception Phase (Gate In) ---
    def register_arrival(self, load_id: int, weight_gross: float = None, ph: float = None, 
                        humidity: float = None, observation: str = None) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        load.register_arrival(weight_gross, ph, humidity, observation)
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    def close_trip(self, load_id: int, data_dict: Dict[str, Any]) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        weight_net = data_dict.get('weight_net')
        ticket = data_dict.get('ticket_number')
        guide = data_dict.get('guide_number')
        ph = data_dict.get('quality_ph')
        humidity = data_dict.get('quality_humidity')
        
        if any(v is None for v in [weight_net, ticket, guide, ph, humidity]):
             raise ValueError("Missing required fields for closing trip")

        load.close_trip(
            weight_net=float(weight_net),
            ticket_number=ticket,
            guide_number=guide,
            ph=float(ph),
            humidity=float(humidity)
        )
        
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    # --- Queries ---
    def get_loads_by_facility(self, facility_id: int) -> List[Load]:
        return self.load_repo.get_all_filtered(origin_facility_id=facility_id)

    def get_loads_by_status(self, status: str) -> List[Load]:
        return self.load_repo.get_by_status(status)
        
    def get_planning_loads(self, status: str) -> List[Load]:
        return self.load_repo.get_loads_with_details(status=status)
    
    def get_in_transit_loads(self) -> List[Load]:
        """Get loads that are in transit."""
        return self.load_repo.get_by_status('InTransit')
    
    def get_assignable_loads(self, vehicle_id: int) -> List[Load]:
        """Get loads assignable to a vehicle."""
        return self.load_repo.get_assignable_loads(vehicle_id)
    
    def get_active_load(self, vehicle_id: int) -> Optional[Load]:
        """Get active load for a vehicle."""
        return self.load_repo.get_active_load(vehicle_id)

    # --- State Transition Engine (New Lifecycle Management) ---
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
            from domain.logistics.entities.load_status import normalize_status
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
        success = self.load_repo.update(load)
        
        # 7. Publicar evento LoadStatusChanged
        if success and self.event_bus:
            from services.common.event_bus import Event, EventTypes
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
            
            # 8. Caso especial: Detectar llegada a campo (destino tipo FIELD)
            if new_status == LoadStatus.AT_DESTINATION and load.destination_site_id:
                self.event_bus.publish(Event(
                    event_type=EventTypes.LOAD_ARRIVED_AT_FIELD,
                    data={
                        'load_id': load_id,
                        'site_id': load.destination_site_id,
                        'timestamp': datetime.now().isoformat()
                    }
                ))
        
        return success

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

    def get_time_in_status(self, load_id: int, status: LoadStatus) -> Optional[timedelta]:
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

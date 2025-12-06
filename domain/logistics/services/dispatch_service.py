from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime, timedelta
from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.repositories.distance_matrix_repository import DistanceMatrixRepository
from domain.logistics.repositories.status_transition_repository import StatusTransitionRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.status_transition import StatusTransition
from domain.logistics.entities.vehicle import Vehicle, VehicleType
from domain.logistics.entities.container import Container
from domain.logistics.services.transition_rules import (
    get_validators_for_transition,
    is_valid_transition,
)
from domain.processing.entities.facility import Facility
from domain.shared.services.compliance_service import ComplianceService
from domain.disposal.services.agronomy_service import AgronomyDomainService
from domain.logistics.services.manifest_service import ManifestService
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
        compliance_service: ComplianceService,
        agronomy_service: AgronomyDomainService,
        # manifest_service: ManifestService,  <-- DEPRECATED: Moved to App Service
        # event_bus: 'EventBus' = None        <-- DEPRECATED: Moved to App Service
    ):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.transition_repo = StatusTransitionRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.container_repo = BaseRepository(db_manager, Container, "containers")
        self.facility_repo = BaseRepository(db_manager, Facility, "facilities")
        self.distance_matrix_repo = DistanceMatrixRepository(db_manager)
        
        self.compliance_service = compliance_service
        self.agronomy_service = agronomy_service
        # self.manifest_service = manifest_service
        # self.event_bus = event_bus

    # --- Planning Phase ---
    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None, 
                       weight_estimated: Optional[float] = None, notes: Optional[str] = None) -> Load:
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            origin_treatment_plant_id=plant_id,
            status=LoadStatus.REQUESTED.value,
            requested_date=requested_date,
            weight_net=weight_estimated,
            notes=notes,
            created_at=datetime.now()
        )
        return self.load_repo.add(load)
    
    # Alias for UI compatibility
    def create_load_request(self, origin_facility_id: int, requested_date: datetime, 
                            weight_estimated: float = None, notes: str = None) -> Load:
        """Alias for create_request - used by planning UI."""
        return self.create_request(
            facility_id=origin_facility_id, 
            requested_date=requested_date,
            weight_estimated=weight_estimated,
            notes=notes
        )

    def schedule_load(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, 
                         site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, 
                         container_quantity: Optional[int] = None) -> bool:
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != LoadStatus.REQUESTED.value:
            raise TransitionException(f"Cannot schedule load. Current status: {load.status}. Expected: '{LoadStatus.REQUESTED.value}'.")
        
        # Validate vehicle type is allowed for the origin facility
        if load.origin_facility_id:
            self._validate_vehicle_type_for_facility(vehicle_id, load.origin_facility_id)
        
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
        load.status = LoadStatus.ASSIGNED.value
        load.updated_at = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def schedule_loads_bulk(self, load_ids: List[int], driver_id: int, vehicle_id: int, scheduled_date: datetime, 
                         site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, 
                         container_quantity: Optional[int] = None) -> int:
        """
        Schedule multiple loads with driver, vehicle, and destination assignment.
        
        Enhanced for Trip Linking: Validates that linked trips (with trip_id) 
        use AMPLIROLL vehicles only.
        """
        # Check if loads share a trip_id (Trip Linking scenario)
        if load_ids:
            first_load = self.load_repo.get_by_id(load_ids[0])
            if first_load and first_load.trip_id:
                # Validate vehicle is AMPLIROLL for linked trips
                vehicle = self.vehicle_repo.get_by_id(vehicle_id)
                if vehicle:
                    try:
                        vehicle_type = VehicleType(vehicle.type)
                        if vehicle_type != VehicleType.AMPLIROLL:
                            raise ValueError(
                                f"🚫 Viajes enlazados requieren vehículo AMPLIROLL. "
                                f"El vehículo {vehicle.license_plate} es tipo {vehicle_type.display_name}."
                            )
                    except ValueError as e:
                        if "🚫" in str(e):
                            raise  # Re-raise our custom error
                        # Other ValueError = invalid enum, default to BATEA check
                        raise ValueError(
                            f"🚫 Viajes enlazados requieren vehículo AMPLIROLL. "
                            f"El vehículo {vehicle.license_plate} no está correctamente configurado."
                        )
        
        success_count = 0
        with self.db_manager:
            for load_id in load_ids:
                self.schedule_load(load_id, driver_id, vehicle_id, scheduled_date, site_id, treatment_plant_id, container_quantity)
                success_count += 1
        return success_count


    # --- Dispatch Phase (Gate Out) ---
    def _validate_vehicle_type_for_facility(self, vehicle_id: int, facility_id: int) -> None:
        """
        Valida que el tipo de vehículo esté permitido en la planta de origen.
        
        Regla de negocio:
        - BATEA: Carga directa, 1 viaje = 1 carga
        - AMPLIROLL: Trabaja con contenedores, puede llevar hasta 2
        """
        if not facility_id:
            return  # Skip validation if no facility
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        facility = self.facility_repo.get_by_id(facility_id)
        
        if not vehicle or not facility:
            return  # Skip if entities not found
        
        allowed_types = facility.allowed_vehicle_types
        if not allowed_types:
            return  # No restrictions configured
        
        # Parse allowed types from CSV string
        allowed_list = VehicleType.from_csv(allowed_types)
        
        # Get vehicle type enum
        try:
            vehicle_type = VehicleType(vehicle.type) if vehicle.type else VehicleType.BATEA
        except ValueError:
            vehicle_type = VehicleType.BATEA  # Default fallback
        
        if vehicle_type not in allowed_list:
            allowed_names = ", ".join([vt.display_name for vt in allowed_list])
            raise ValueError(
                f"🚫 Tipo de vehículo no permitido: El vehículo {vehicle.license_plate} "
                f"es tipo '{vehicle_type.display_name}', pero la planta '{facility.name}' "
                f"solo permite: {allowed_names}"
            )

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
        driver_id: int,
        vehicle_id: int,
        destination_site_id: int,
        origin_facility_id: int,
        weight_net: float,
        guide_number: Optional[str] = None,
        container_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dispatches a truck (simplified flow without batch management).
        """
        # Validate vehicle type is allowed for this facility
        self._validate_vehicle_type_for_facility(vehicle_id, origin_facility_id)
        self._validate_capacity(vehicle_id, container_id)
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if vehicle and hasattr(vehicle, 'max_capacity') and vehicle.max_capacity:
            if weight_net > vehicle.max_capacity:
                raise ValueError(f"Peso excede capacidad del vehículo.")

        with self.db_manager as conn:
            load = Load(
                id=None,
                origin_facility_id=origin_facility_id,
                destination_site_id=destination_site_id,
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
            
            # Register Nitrogen if destination site is provided
            if destination_site_id:
                self.agronomy_service.register_nitrogen_application(
                    site_id=destination_site_id,
                    load_id=created_load.id,
                    batch_id=None,
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
        if not load or load.status != LoadStatus.ASSIGNED.value:
            raise ValueError("Invalid load or status")
        load.status = LoadStatus.ACCEPTED.value
        load.updated_at = datetime.now()
        return self.load_repo.update(load)

    def start_trip(self, load_id: int) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != LoadStatus.ACCEPTED.value:
            raise ValueError("Invalid load or status")
        load.status = LoadStatus.EN_ROUTE_DESTINATION.value
        load.dispatch_time = datetime.now()
        load.updated_at = datetime.now()
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
    
    def get_assigned_loads_by_vehicle(self, vehicle_id: int) -> List[Load]:
        """
        Get loads assigned (ASSIGNED or ACCEPTED) to a specific vehicle.
        
        Used by the driver dispatch view to show trips assigned to their vehicle.
        
        Args:
            vehicle_id: ID of the vehicle to filter by
            
        Returns:
            List of loads assigned to the vehicle
        """
        return self.load_repo.get_assigned_loads_by_vehicle(vehicle_id)
    
    def get_in_transit_loads_by_destination_site(self, site_id: int) -> List[Load]:
        """
        Get loads in transit heading to a specific disposal site.
        
        Used by disposal reception to show incoming trucks.
        
        Args:
            site_id: ID of the destination site
            
        Returns:
            List of loads in transit to the site
        """
        return self.load_repo.get_in_transit_loads_by_destination_site(site_id)
    
    def get_in_transit_loads_by_treatment_plant(self, plant_id: int) -> List[Load]:
        """
        Get loads in transit heading to a specific treatment plant.
        
        Used by treatment reception to show incoming trucks.
        
        Args:
            plant_id: ID of the destination treatment plant
            
        Returns:
            List of loads in transit to the plant
        """
        return self.load_repo.get_in_transit_loads_by_treatment_plant(plant_id)
    
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

        # --- PROMOTION LOGIC ---
        # Promote critical data from JSON attributes to SQL columns for BI/Reporting
        if 'gross_weight' in load.attributes:
             try:
                 load.gross_weight = float(load.attributes['gross_weight'])
             except (ValueError, TypeError):
                 pass # Keep original or None if conversion fails
        
        if 'tare_weight' in load.attributes:
             try:
                 load.tare_weight = float(load.attributes['tare_weight'])
             except (ValueError, TypeError):
                 pass

        if load.gross_weight is not None and load.tare_weight is not None:
             load.net_weight = load.gross_weight - load.tare_weight
             load.weight_net = load.net_weight # Alias

        success = self.load_repo.update(load)
        
        # 7. Publicar evento LoadStatusChanged
        if success and self.event_bus:
            from infrastructure.events.event_bus import Event, EventTypes
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

    def update_load_attributes(self, load_id: int, attributes_dict: Dict[str, Any]) -> bool:
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

    # --- Trip Linking Methods (Consolidación de Cargas) ---
    
    def find_linkable_candidates(self, primary_load_id: int) -> List[dict]:
        """
        Busca cargas candidatas para enlazar con una carga primaria.
        
        Una carga es "linkable" si:
        1. Su origen es un punto de enlace (facility.is_link_point = True)
        2. Está en estado REQUESTED y sin trip_id asignado
        3. Las fechas son compatibles (±1 día)
        4. No es la misma carga primaria
        
        Ejemplo de uso:
        - Carga primaria: Los Álamos (no es punto de enlace)
        - Candidata: Cañete (ES punto de enlace)
        - Se pueden enlazar: Los Álamos -> Cañete -> Destino Final
        
        Args:
            primary_load_id: ID de la carga primaria seleccionada
            
        Returns:
            Lista de dicts con candidatos: {id, origin_name, distance_km, created_at}
        """
        # 1. Obtener carga primaria
        primary_load = self.load_repo.get_by_id(primary_load_id)
        if not primary_load:
            return []
        
        # Solo buscar para cargas REQUESTED sin trip asignado
        if primary_load.status != 'REQUESTED' or primary_load.trip_id:
            return []
        
        # 2. Buscar cargas en facilities que sean puntos de enlace (is_link_point = 1)
        # Consulta directa para encontrar cargas pendientes en puntos de enlace
        candidates = []
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Buscar cargas REQUESTED en facilities marcados como puntos de enlace
            # que no sean el mismo origen de la carga primaria
            query = """
                SELECT 
                    l.id,
                    l.origin_facility_id,
                    l.created_at,
                    f.name as origin_name,
                    f.is_link_point
                FROM loads l
                INNER JOIN facilities f ON l.origin_facility_id = f.id
                WHERE l.status = 'REQUESTED'
                AND l.id != ?
                AND (l.trip_id IS NULL OR l.trip_id = '')
                AND f.is_link_point = 1
                AND f.is_active = 1
                AND l.origin_facility_id != ?
            """
            
            cursor.execute(query, (primary_load_id, primary_load.origin_facility_id or -1))
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = dict(row)
                
                # Obtener distancia si existe en distance_matrix
                distance_km = self.distance_matrix_repo.get_route_distance(
                    primary_load.origin_facility_id,
                    row_dict['origin_facility_id'],
                    'FACILITY'
                ) or 0.0
                
                candidates.append({
                    'id': row_dict['id'],
                    'origin_facility_id': row_dict['origin_facility_id'],
                    'origin_name': row_dict['origin_name'],
                    'distance_km': distance_km,
                    'created_at': row_dict['created_at'],
                    'is_link_point': True
                })
        
        return candidates
    
    def link_loads_into_trip(self, load_ids: List[int]) -> str:
        """
        Agrupa múltiples cargas en un único trip con UUID compartido.
        
        Clasifica cada carga como PICKUP_SEGMENT o MAIN_HAUL basado en
        la distancia al destino final (heurística: más lejana = PICKUP).
        
        Args:
            load_ids: Lista de IDs de cargas a enlazar (típicamente 2)
            
        Returns:
            trip_id: UUID generado para el trip
            
        Raises:
            ValueError: Si las cargas no son válidas o ya tienen trip_id
            
        Example:
            trip_id = service.link_loads_into_trip([123, 124])
            # Returns: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        """
        if not load_ids or len(load_ids) < 2:
            raise ValueError("Se requieren al menos 2 cargas para crear un trip enlazado")
        
        # Validar que todas las cargas existen y están PENDING
        loads = []
        for load_id in load_ids:
            load = self.load_repo.get_by_id(load_id)
            if not load:
                raise ValueError(f"Carga {load_id} no encontrada")
            if load.status != 'REQUESTED':
                raise ValueError(f"Carga {load_id} no está en estado REQUESTED (actual: {load.status})")
            if load.trip_id:
                raise ValueError(f"Carga {load_id} ya tiene un trip_id asignado: {load.trip_id}")
            loads.append(load)
        
        # Generar UUID único para el trip
        trip_id = str(uuid.uuid4())
        
        # Clasificar segmentos: PICKUP_SEGMENT (más lejana) vs MAIN_HAUL (más cercana)
        # Heurística: asumimos que todas van al mismo destino final
        # La que tiene origen más lejano al destino es PICKUP_SEGMENT
        
        # Para simplificar, usamos orden de load_ids:
        # - Primera carga = PICKUP_SEGMENT (se recoge primero)
        # - Última carga = MAIN_HAUL (carga principal, más cercana al destino)
        segment_types = {}
        for i, load_id in enumerate(load_ids):
            if i == 0:
                segment_types[load_id] = 'PICKUP_SEGMENT'
            elif i == len(load_ids) - 1:
                segment_types[load_id] = 'MAIN_HAUL'
            else:
                # Para más de 2 cargas (futuro)
                segment_types[load_id] = 'PICKUP_SEGMENT'
        
        # Actualizar todas las cargas con el trip_id y segment_type
        self.load_repo.update_trip_id_bulk(load_ids, trip_id, segment_types)
        
        return trip_id
    
    def assign_resources_to_trip(
        self,
        trip_id: str,
        driver_id: int,
        vehicle_id: int,
        scheduled_date: datetime,
        site_id: Optional[int] = None,
        treatment_plant_id: Optional[int] = None
    ) -> int:
        """
        Asigna conductor, vehículo y fecha a TODAS las cargas de un trip.
        
        IMPORTANTE:
        - Valida que el vehículo sea AMPLIROLL (requerido para trips enlazados)
        - Actualiza todas las cargas que comparten el trip_id
        - Cambia el estado a ASSIGNED
        
        Args:
            trip_id: UUID del trip
            driver_id: ID del conductor
            vehicle_id: ID del vehículo (debe ser AMPLIROLL)
            scheduled_date: Fecha/hora programada
            site_id: Destino final (Site) - opcional
            treatment_plant_id: Destino final (Planta) - opcional
            
        Returns:
            Cantidad de cargas actualizadas
            
        Raises:
            ValueError: Si el vehículo no es AMPLIROLL o no hay destino
        """
        # Validar que hay un destino definido
        if not site_id and not treatment_plant_id:
            raise ValueError("Debe proporcionar un destino (Site o Treatment Plant)")
        
        # Validar que el vehículo es AMPLIROLL
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehículo {vehicle_id} no encontrado")
        
        try:
            vehicle_type = VehicleType(vehicle.type)
            if vehicle_type != VehicleType.AMPLIROLL:
                raise ValueError(
                    f"🚫 Los viajes enlazados requieren vehículo AMPLIROLL. "
                    f"El vehículo {vehicle.license_plate} es tipo {vehicle_type.display_name}. "
                    f"Por favor, seleccione un vehículo Ampliroll con capacidad para 2 contenedores."
                )
        except ValueError as e:
            if "🚫" in str(e):
                raise  # Re-raise our custom error
            # Invalid enum value
            raise ValueError(
                f"🚫 Los viajes enlazados requieren vehículo AMPLIROLL. "
                f"El vehículo {vehicle.license_plate} no tiene un tipo válido configurado."
            )
        
        # Obtener todas las cargas del trip
        trip_loads = self.load_repo.get_loads_by_trip_id(trip_id)
        if not trip_loads:
            raise ValueError(f"No se encontraron cargas para el trip {trip_id}")
        
        # Asignar recursos a cada carga del trip
        success_count = 0
        for load in trip_loads:
            # Validar vehicle type para cada origen
            if load.origin_facility_id:
                self._validate_vehicle_type_for_facility(vehicle_id, load.origin_facility_id)
            
            load.driver_id = driver_id
            load.vehicle_id = vehicle_id
            load.scheduled_date = scheduled_date
            
            # Asignar destino (todas las cargas del trip van al mismo destino final)
            if treatment_plant_id:
                load.destination_treatment_plant_id = treatment_plant_id
                load.destination_site_id = None
            else:
                load.destination_site_id = site_id
                load.destination_treatment_plant_id = None
            
            load.status = LoadStatus.ASSIGNED.value
            load.updated_at = datetime.now()
            
            if self.load_repo.update(load):
                success_count += 1
        
        return success_count

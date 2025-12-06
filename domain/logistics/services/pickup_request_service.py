"""
Servicio para gestión de solicitudes de retiro del cliente.
"""
from typing import List, Optional
from datetime import datetime, date
from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.entities.pickup_request import PickupRequest, PickupRequestStatus
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.vehicle import VehicleType
from domain.processing.entities.facility import Facility


class PickupRequestService:
    """
    Servicio para gestionar solicitudes de retiro de clientes.
    
    Flujo:
    1. Cliente crea PickupRequest (N cargas, tipo vehículo, contenedores)
    2. Sistema genera N registros Load en estado REQUESTED
    3. Planificador asigna recursos a cada Load
    4. Estado del PickupRequest se actualiza según progreso de Loads
    """
    
    def __init__(self, db_manager: DatabaseManager, facility_repo: BaseRepository):
        self.db_manager = db_manager
        self.pickup_repo = BaseRepository(db_manager, PickupRequest, "pickup_requests")
        self.load_repo = BaseRepository(db_manager, Load, "loads")
        self.facility_repo = facility_repo
    
    def create_pickup_request(
        self,
        client_id: int,
        facility_id: int,
        requested_date: date,
        vehicle_type: str,
        load_quantity: int,
        containers_per_load: Optional[int] = None,
        notes: Optional[str] = None
    ) -> PickupRequest:
        """
        Crea una solicitud de retiro y genera las cargas asociadas.
        
        Args:
            client_id: ID del cliente solicitante
            facility_id: ID de la planta de origen
            requested_date: Fecha solicitada para los retiros
            vehicle_type: BATEA o AMPLIROLL
            load_quantity: Cantidad de cargas/retiros
            containers_per_load: Contenedores por carga (solo AMPLIROLL, 1-2)
            notes: Observaciones
            
        Returns:
            PickupRequest creado con sus cargas asociadas
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validaciones
        self._validate_request(facility_id, vehicle_type, load_quantity, containers_per_load)
        
        with self.db_manager as conn:
            # 1. Crear el PickupRequest
            pickup_request = PickupRequest(
                id=None,
                client_id=client_id,
                facility_id=facility_id,
                requested_date=requested_date,
                vehicle_type=vehicle_type,
                load_quantity=load_quantity,
                containers_per_load=containers_per_load,
                notes=notes,
                status=PickupRequestStatus.PENDING.value,
                created_at=datetime.now()
            )
            
            created_request = self.pickup_repo.add(pickup_request)
            
            # 2. Generar N cargas individuales
            for i in range(load_quantity):
                load = Load(
                    id=None,
                    origin_facility_id=facility_id,
                    vehicle_id=None,  # Sin asignar - lo asigna el planificador
                    driver_id=None,   # Sin asignar - lo asigna el planificador
                    destination_site_id=None,  # Sin asignar - lo asigna el planificador
                    pickup_request_id=created_request.id,
                    vehicle_type_requested=vehicle_type,
                    container_quantity=containers_per_load if vehicle_type == "AMPLIROLL" else None,
                    status=LoadStatus.REQUESTED.value,
                    requested_date=datetime.combine(requested_date, datetime.min.time()),
                    created_at=datetime.now()
                )
                self.load_repo.add(load)
            
            return created_request
    
    def _validate_request(
        self,
        facility_id: int,
        vehicle_type: str,
        load_quantity: int,
        containers_per_load: Optional[int]
    ) -> None:
        """Valida los datos de la solicitud."""
        # Validar tipo de vehículo
        if vehicle_type not in [VehicleType.BATEA.value, VehicleType.AMPLIROLL.value]:
            raise ValueError(f"Tipo de vehículo inválido: {vehicle_type}")
        
        # Validar cantidad de cargas
        if load_quantity < 1 or load_quantity > 50:
            raise ValueError("La cantidad de cargas debe estar entre 1 y 50")
        
        # Validar contenedores para AMPLIROLL
        if vehicle_type == VehicleType.AMPLIROLL.value:
            if containers_per_load is None or containers_per_load < 1 or containers_per_load > 2:
                raise ValueError("AMPLIROLL requiere 1 o 2 contenedores por carga")
        
        # Validar que la planta permite el tipo de vehículo
        facility = self.facility_repo.get_by_id(facility_id)
        if facility and facility.allowed_vehicle_types:
            allowed = VehicleType.from_csv(facility.allowed_vehicle_types)
            try:
                requested_type = VehicleType(vehicle_type)
                if requested_type not in allowed:
                    allowed_names = ", ".join([t.display_name for t in allowed])
                    raise ValueError(
                        f"La planta '{facility.name}' no permite vehículos tipo "
                        f"'{requested_type.display_name}'. Tipos permitidos: {allowed_names}"
                    )
            except ValueError as e:
                if "not a valid" in str(e):
                    raise ValueError(f"Tipo de vehículo inválido: {vehicle_type}")
                raise
    
    def get_by_id(self, pickup_request_id: int) -> Optional[PickupRequest]:
        """Obtiene una solicitud por ID."""
        return self.pickup_repo.get_by_id(pickup_request_id)
    
    def get_by_client(self, client_id: int, include_completed: bool = False) -> List[PickupRequest]:
        """Obtiene solicitudes de un cliente."""
        requests = self.pickup_repo.get_all_filtered(client_id=client_id)
        if not include_completed:
            requests = [r for r in requests if r.status != PickupRequestStatus.COMPLETED.value]
        return self._enrich_with_counts(requests)
    
    def get_by_facility(self, facility_id: int) -> List[PickupRequest]:
        """Obtiene solicitudes de una planta."""
        requests = self.pickup_repo.get_all_filtered(facility_id=facility_id)
        return self._enrich_with_counts(requests)
    
    def get_pending_requests(self) -> List[PickupRequest]:
        """Obtiene todas las solicitudes pendientes de programar."""
        all_requests = self.pickup_repo.get_all()
        pending = [r for r in all_requests if r.status in [
            PickupRequestStatus.PENDING.value,
            PickupRequestStatus.PARTIALLY_SCHEDULED.value
        ]]
        return self._enrich_with_counts(pending)
    
    def get_loads_for_request(self, pickup_request_id: int) -> List[Load]:
        """Obtiene las cargas asociadas a una solicitud."""
        return self.load_repo.get_all_filtered(pickup_request_id=pickup_request_id)
    
    def _enrich_with_counts(self, requests: List[PickupRequest]) -> List[PickupRequest]:
        """Enriquece las solicitudes con conteo de cargas programadas."""
        for request in requests:
            loads = self.get_loads_for_request(request.id)
            scheduled = sum(1 for l in loads if l.status not in [
                LoadStatus.REQUESTED.value, 'CREATED'
            ])
            request.scheduled_count = scheduled
        return requests
    
    def update_request_status(self, pickup_request_id: int) -> None:
        """Actualiza el estado de la solicitud basándose en sus cargas."""
        request = self.pickup_repo.get_by_id(pickup_request_id)
        if not request:
            return
        
        loads = self.get_loads_for_request(pickup_request_id)
        
        scheduled = 0
        in_transit = 0
        completed = 0
        
        for load in loads:
            if load.status in ['COMPLETED', 'DELIVERED', 'CLOSED']:
                completed += 1
            elif load.status in ['IN_TRANSIT', 'InTransit', 'EN_ROUTE_DESTINATION']:
                in_transit += 1
            elif load.status not in [LoadStatus.REQUESTED.value, 'CREATED']:
                scheduled += 1
        
        request.update_status_from_loads(scheduled, completed, in_transit)
        request.updated_at = datetime.now()
        self.pickup_repo.update(request)
    
    def cancel_request(self, pickup_request_id: int) -> bool:
        """Cancela una solicitud y sus cargas pendientes."""
        request = self.pickup_repo.get_by_id(pickup_request_id)
        if not request:
            return False
        
        # Solo cancelar cargas que no han iniciado
        loads = self.get_loads_for_request(pickup_request_id)
        for load in loads:
            if load.status in [LoadStatus.REQUESTED.value, 'CREATED', 'ASSIGNED']:
                load.status = 'CANCELLED'
                load.updated_at = datetime.now()
                self.load_repo.update(load)
        
        request.status = PickupRequestStatus.CANCELLED.value
        request.updated_at = datetime.now()
        return self.pickup_repo.update(request)

    # ==========================================
    # Métodos para Solicitudes de Planta de Tratamiento (DS4)
    # ==========================================
    
    def create_treatment_plant_request(
        self,
        treatment_plant_id: int,
        requested_date: date,
        load_quantity: int,
        notes: Optional[str] = None
    ) -> PickupRequest:
        """
        Crea una solicitud de retiro desde planta de tratamiento (DS4).
        
        Las solicitudes de planta de tratamiento siempre usan:
        - Vehículo: AMPLIROLL
        - Contenedores por carga: 2
        - Sin client_id (solicitud interna)
        
        Args:
            treatment_plant_id: ID de la planta de tratamiento de origen
            requested_date: Fecha solicitada para los retiros
            load_quantity: Cantidad de camiones/retiros
            notes: Observaciones
            
        Returns:
            PickupRequest creado con sus cargas asociadas
        """
        # Validar cantidad de cargas
        if load_quantity < 1 or load_quantity > 50:
            raise ValueError("La cantidad de cargas debe estar entre 1 y 50")
        
        vehicle_type = VehicleType.AMPLIROLL.value
        containers_per_load = 2  # Siempre 2 contenedores para DS4
        
        with self.db_manager as conn:
            # 1. Crear el PickupRequest
            pickup_request = PickupRequest(
                id=None,
                client_id=None,  # Solicitud interna
                facility_id=None,  # No hay facility de cliente
                treatment_plant_id=treatment_plant_id,
                requested_date=requested_date,
                vehicle_type=vehicle_type,
                load_quantity=load_quantity,
                containers_per_load=containers_per_load,
                notes=notes,
                status=PickupRequestStatus.PENDING.value,
                created_at=datetime.now()
            )
            
            created_request = self.pickup_repo.add(pickup_request)
            
            # 2. Generar N cargas individuales
            for i in range(load_quantity):
                load = Load(
                    id=None,
                    origin_facility_id=None,  # No hay facility de cliente
                    origin_treatment_plant_id=treatment_plant_id,  # Planta de tratamiento como origen
                    vehicle_id=None,
                    driver_id=None,
                    destination_site_id=None,
                    pickup_request_id=created_request.id,
                    vehicle_type_requested=vehicle_type,
                    container_quantity=containers_per_load,
                    status=LoadStatus.REQUESTED.value,
                    requested_date=datetime.combine(requested_date, datetime.min.time()),
                    created_at=datetime.now()
                )
                self.load_repo.add(load)
            
            return created_request
    
    def get_by_treatment_plant(self, treatment_plant_id: int, include_completed: bool = False) -> List[PickupRequest]:
        """Obtiene solicitudes de una planta de tratamiento."""
        requests = self.pickup_repo.get_all_filtered(treatment_plant_id=treatment_plant_id)
        if not include_completed:
            requests = [r for r in requests if r.status != PickupRequestStatus.COMPLETED.value]
        return self._enrich_with_counts(requests)

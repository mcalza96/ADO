"""
LoadDispatchService - Maneja el despacho y aceptación de cargas.

Responsabilidades:
- Despacho de vehículos (gate out)
- Aceptación de viajes por conductores
- Inicio de tránsito (en ruta)
- Validaciones de capacidad y compatibilidad
- Generación de manifiestos de transporte
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.vehicle import Vehicle
from domain.logistics.entities.container import Container
from domain.processing.entities.facility import Facility
from domain.shared.constants import SLUDGE_DENSITY


class LoadDispatchService:
    """
    Servicio especializado en despacho de cargas.
    
    Gestiona la salida física de vehículos desde plantas de tratamiento
    y el inicio del viaje hacia el destino.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.container_repo = BaseRepository(db_manager, Container, "containers")
        self.facility_repo = BaseRepository(db_manager, Facility, "facilities")

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
        Despacha un camión directamente (flujo simplificado sin batch).
        
        Crea una carga en estado InTransit directamente.
        Usado en flujo legacy de despacho directo.
        
        Args:
            driver_id: Conductor
            vehicle_id: Vehículo
            destination_site_id: Sitio de destino
            origin_facility_id: Planta de origen
            weight_net: Peso neto en toneladas
            guide_number: Número de guía de despacho
            container_id: Contenedor (opcional, para AMPLIROLL)
            
        Returns:
            Dict con status, load_id, manifest_code, manifest_path
            
        Raises:
            ValueError: Si validaciones de capacidad o tipo fallan
        """
        # Nota: Las validaciones de tipo y capacidad fueron movidas a LoadPlanningService
        # Este método asume que la carga ya fue validada en planificación
        
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
            
            # Nota: La generación de manifiesto y registro de nitrógeno
            # deben ser manejados por servicios de aplicación que coordinen
            # múltiples dominios (ManifestService, AgronomyService)
            
            return {
                "status": "success",
                "load_id": created_load.id,
                "manifest_code": created_load.manifest_code,
                "guide_number": guide_number
            }

    def accept_trip(self, load_id: int) -> bool:
        """
        Conductor acepta el viaje asignado.
        
        Transición: ASSIGNED -> ACCEPTED
        
        Args:
            load_id: ID de la carga
            
        Returns:
            True si la aceptación fue exitosa
            
        Raises:
            ValueError: Si la carga no existe o no está en estado ASSIGNED
        """
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != LoadStatus.ASSIGNED.value:
            raise ValueError("Invalid load or status")
        
        load.status = LoadStatus.ACCEPTED.value
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    def start_trip(self, load_id: int) -> bool:
        """
        Inicia el viaje (conductor sale de planta).
        
        Transición: ACCEPTED -> EN_ROUTE_DESTINATION
        
        Args:
            load_id: ID de la carga
            
        Returns:
            True si el inicio fue exitoso
            
        Raises:
            ValueError: Si la carga no existe o no está en estado ACCEPTED
        """
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != LoadStatus.ACCEPTED.value:
            raise ValueError("Invalid load or status")
        
        load.status = LoadStatus.EN_ROUTE_DESTINATION.value
        load.dispatch_time = datetime.now()
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    # --- Query Methods ---
    
    def get_in_transit_loads(self) -> List[Load]:
        """
        Obtiene cargas en tránsito (en ruta hacia destino).
        
        Returns:
            Lista de cargas con estado InTransit o EN_ROUTE_DESTINATION
        """
        return self.load_repo.get_by_status('InTransit')
    
    def get_assignable_loads(self, vehicle_id: int) -> List[Load]:
        """
        Obtiene cargas que pueden ser asignadas a un vehículo específico.
        
        Args:
            vehicle_id: ID del vehículo
            
        Returns:
            Lista de cargas asignables
        """
        return self.load_repo.get_assignable_loads(vehicle_id)
    
    def get_assigned_loads_by_vehicle(self, vehicle_id: int) -> List[Load]:
        """
        Obtiene cargas asignadas (ASSIGNED o ACCEPTED) a un vehículo.
        
        Usado por la vista de despacho de conductores para mostrar
        los viajes asignados a su vehículo.
        
        Args:
            vehicle_id: ID del vehículo
            
        Returns:
            Lista de cargas asignadas al vehículo
        """
        return self.load_repo.get_assigned_loads_by_vehicle(vehicle_id)
    
    def get_active_load(self, vehicle_id: int) -> Optional[Load]:
        """
        Obtiene la carga activa para un vehículo.
        
        Una carga es "activa" si está en estado:
        - ACCEPTED
        - EN_ROUTE_DESTINATION
        - AT_DESTINATION
        
        Args:
            vehicle_id: ID del vehículo
            
        Returns:
            La carga activa o None si no hay ninguna
        """
        return self.load_repo.get_active_load(vehicle_id)

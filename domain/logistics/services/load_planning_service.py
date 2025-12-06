"""
LoadPlanningService - Maneja la planificación y programación de cargas.

Responsabilidades:
- Crear solicitudes de carga (load requests)
- Asignar recursos (driver, vehicle, destination)
- Programación de fechas de recolección/entrega
- Validación de compatibilidad vehículo-planta
- Programación masiva (bulk scheduling)
"""

from typing import Optional, List
from datetime import datetime

from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.vehicle import Vehicle, VehicleType
from domain.logistics.entities.container import Container
from domain.processing.entities.facility import Facility
from domain.shared.exceptions import TransitionException
from domain.shared.constants import SLUDGE_DENSITY


class LoadPlanningService:
    """
    Servicio especializado en planificación de cargas.
    
    Gestiona la creación de solicitudes y la asignación de recursos
    antes del despacho físico del vehículo.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.container_repo = BaseRepository(db_manager, Container, "containers")
        self.facility_repo = BaseRepository(db_manager, Facility, "facilities")

    def create_request(
        self,
        facility_id: Optional[int],
        requested_date: datetime,
        plant_id: Optional[int] = None,
        weight_estimated: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Load:
        """
        Crea una solicitud de carga sin asignar recursos.
        
        Estado inicial: REQUESTED
        
        Args:
            facility_id: Planta de origen (PTAS)
            requested_date: Fecha solicitada para recolección
            plant_id: Planta de tratamiento de origen (alternativo)
            weight_estimated: Peso estimado en toneladas
            notes: Notas adicionales
            
        Returns:
            Load creada con estado REQUESTED
        """
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
    
    def create_load_request(
        self,
        origin_facility_id: int,
        requested_date: datetime,
        weight_estimated: float = None,
        notes: str = None
    ) -> Load:
        """
        Alias para create_request - usado por UI de planificación.
        
        Mantiene compatibilidad con código legacy.
        """
        return self.create_request(
            facility_id=origin_facility_id, 
            requested_date=requested_date,
            weight_estimated=weight_estimated,
            notes=notes
        )

    def schedule_load(
        self,
        load_id: int,
        driver_id: int,
        vehicle_id: int,
        scheduled_date: datetime,
        site_id: Optional[int] = None,
        treatment_plant_id: Optional[int] = None,
        container_quantity: Optional[int] = None
    ) -> bool:
        """
        Programa una carga asignando recursos y destino.
        
        Transición: REQUESTED -> ASSIGNED
        
        Args:
            load_id: ID de la carga a programar
            driver_id: Conductor asignado
            vehicle_id: Vehículo asignado
            scheduled_date: Fecha programada para el servicio
            site_id: Sitio de disposición (opcional)
            treatment_plant_id: Planta de tratamiento destino (opcional)
            container_quantity: Cantidad de contenedores (para AMPLIROLL)
            
        Returns:
            True si la programación fue exitosa
            
        Raises:
            ValueError: Si falta destino o la carga no existe
            TransitionException: Si el estado actual no es REQUESTED
        """
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != LoadStatus.REQUESTED.value:
            raise TransitionException(
                f"Cannot schedule load. Current status: {load.status}. "
                f"Expected: '{LoadStatus.REQUESTED.value}'."
            )
        
        # Validar que el tipo de vehículo sea compatible con la planta
        if load.origin_facility_id:
            self._validate_vehicle_type_for_facility(vehicle_id, load.origin_facility_id)
        
        # Asignar recursos
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.container_quantity = container_quantity
        
        # Asignar destino
        if treatment_plant_id:
            load.destination_treatment_plant_id = treatment_plant_id
            load.destination_site_id = None
        else:
            load.destination_site_id = site_id
            load.destination_treatment_plant_id = None
            
        # Actualizar estado y fecha
        load.scheduled_date = scheduled_date
        load.status = LoadStatus.ASSIGNED.value
        load.updated_at = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def schedule_loads_bulk(
        self,
        load_ids: List[int],
        driver_id: int,
        vehicle_id: int,
        scheduled_date: datetime,
        site_id: Optional[int] = None,
        treatment_plant_id: Optional[int] = None,
        container_quantity: Optional[int] = None
    ) -> int:
        """
        Programa múltiples cargas con los mismos recursos.
        
        Útil para:
        - Asignación masiva de un conductor a varias cargas
        - Planificación de viajes enlazados (trip linking)
        
        Enhanced: Valida que viajes enlazados usen vehículos AMPLIROLL.
        
        Args:
            load_ids: Lista de IDs de cargas a programar
            driver_id: Conductor asignado
            vehicle_id: Vehículo asignado
            scheduled_date: Fecha programada
            site_id: Sitio de disposición (opcional)
            treatment_plant_id: Planta de tratamiento destino (opcional)
            container_quantity: Cantidad de contenedores (para AMPLIROLL)
            
        Returns:
            Cantidad de cargas programadas exitosamente
            
        Raises:
            ValueError: Si viajes enlazados no usan AMPLIROLL
        """
        # Validación especial para viajes enlazados
        if load_ids:
            first_load = self.load_repo.get_by_id(load_ids[0])
            if first_load and first_load.trip_id:
                # Validar que el vehículo sea AMPLIROLL para viajes enlazados
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
                            raise  # Re-lanzar error personalizado
                        # ValueError de enum inválido
                        raise ValueError(
                            f"🚫 Viajes enlazados requieren vehículo AMPLIROLL. "
                            f"El vehículo {vehicle.license_plate} no está correctamente configurado."
                        )
        
        # Programar todas las cargas en transacción
        success_count = 0
        with self.db_manager:
            for load_id in load_ids:
                self.schedule_load(
                    load_id, driver_id, vehicle_id, scheduled_date,
                    site_id, treatment_plant_id, container_quantity
                )
                success_count += 1
        return success_count

    def _validate_vehicle_type_for_facility(
        self,
        vehicle_id: int,
        facility_id: int
    ) -> None:
        """
        Valida que el tipo de vehículo esté permitido en la planta de origen.
        
        Regla de negocio:
        - BATEA: Carga directa, 1 viaje = 1 carga
        - AMPLIROLL: Trabaja con contenedores, puede llevar hasta 2
        
        Args:
            vehicle_id: ID del vehículo
            facility_id: ID de la planta
            
        Raises:
            ValueError: Si el tipo de vehículo no está permitido
        """
        if not facility_id:
            return  # Skip validation si no hay planta
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        facility = self.facility_repo.get_by_id(facility_id)
        
        if not vehicle or not facility:
            return  # Skip si no se encuentran las entidades
        
        allowed_types = facility.allowed_vehicle_types
        if not allowed_types:
            return  # Sin restricciones configuradas
        
        # Parsear tipos permitidos desde CSV
        allowed_list = VehicleType.from_csv(allowed_types)
        
        # Obtener tipo de vehículo como enum
        try:
            vehicle_type = VehicleType(vehicle.type) if vehicle.type else VehicleType.BATEA
        except ValueError:
            vehicle_type = VehicleType.BATEA  # Fallback por defecto
        
        if vehicle_type not in allowed_list:
            allowed_names = ", ".join([vt.display_name for vt in allowed_list])
            raise ValueError(
                f"🚫 Tipo de vehículo no permitido: El vehículo {vehicle.license_plate} "
                f"es tipo '{vehicle_type.display_name}', pero la planta '{facility.name}' "
                f"solo permite: {allowed_names}"
            )

    def _validate_capacity(
        self,
        vehicle_id: int,
        container_id: Optional[int]
    ) -> None:
        """
        Valida que la capacidad del contenedor no exceda la del vehículo.
        
        Args:
            vehicle_id: ID del vehículo
            container_id: ID del contenedor (opcional)
            
        Raises:
            ValueError: Si el peso estimado excede la capacidad del vehículo
        """
        if not container_id:
            return 
        
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        container = self.container_repo.get_by_id(container_id)
        
        if not vehicle or not container:
            return 
            
        estimated_weight = container.capacity_m3 * SLUDGE_DENSITY
        if estimated_weight > vehicle.capacity_wet_tons:
            raise ValueError(
                f"Capacity Risk: Container {container.code} ({container.capacity_m3}m3) "
                f"estimated weight ({estimated_weight:.2f}t) exceeds Vehicle "
                f"{vehicle.license_plate} capacity ({vehicle.capacity_wet_tons}t)."
            )

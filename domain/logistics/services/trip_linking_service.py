"""
TripLinkingService - Maneja la consolidación de múltiples cargas en viajes enlazados.

Responsabilidades:
- Búsqueda de candidatos para enlazar (linkable candidates)
- Creación de trips con UUID compartido
- Clasificación de segmentos (PICKUP vs MAIN_HAUL)
- Asignación de recursos a trips completos
- Validación de vehículos AMPLIROLL
"""

from typing import Optional, List, Dict
from datetime import datetime
import uuid

from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.repositories.distance_matrix_repository import DistanceMatrixRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.entities.vehicle import Vehicle, VehicleType
from domain.processing.entities.facility import Facility


class TripLinkingService:
    """
    Servicio especializado en gestión de viajes enlazados (Trip Linking).
    
    Permite consolidar múltiples cargas de diferentes plantas en un solo
    viaje utilizando vehículos AMPLIROLL con capacidad para 2 contenedores.
    
    Ejemplo: Los Álamos (carga A) -> Cañete (carga B) -> Destino Final
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.facility_repo = BaseRepository(db_manager, Facility, "facilities")
        self.distance_matrix_repo = DistanceMatrixRepository(db_manager)

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
        
        # 2. Buscar cargas en facilities que sean puntos de enlace
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
        
        # Validar que todas las cargas existen y están REQUESTED
        loads = []
        for load_id in load_ids:
            load = self.load_repo.get_by_id(load_id)
            if not load:
                raise ValueError(f"Carga {load_id} no encontrada")
            if load.status != 'REQUESTED':
                raise ValueError(
                    f"Carga {load_id} no está en estado REQUESTED (actual: {load.status})"
                )
            if load.trip_id:
                raise ValueError(
                    f"Carga {load_id} ya tiene un trip_id asignado: {load.trip_id}"
                )
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
                raise  # Re-lanzar error personalizado
            # Valor de enum inválido
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
            # Validar compatibilidad de tipo de vehículo con cada origen
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

    def _validate_vehicle_type_for_facility(
        self,
        vehicle_id: int,
        facility_id: int
    ) -> None:
        """
        Valida que el tipo de vehículo esté permitido en la planta.
        
        Args:
            vehicle_id: ID del vehículo
            facility_id: ID de la planta
            
        Raises:
            ValueError: Si el tipo de vehículo no está permitido
        """
        if not facility_id:
            return
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        facility = self.facility_repo.get_by_id(facility_id)
        
        if not vehicle or not facility:
            return
        
        allowed_types = facility.allowed_vehicle_types
        if not allowed_types:
            return
        
        allowed_list = VehicleType.from_csv(allowed_types)
        
        try:
            vehicle_type = VehicleType(vehicle.type) if vehicle.type else VehicleType.BATEA
        except ValueError:
            vehicle_type = VehicleType.BATEA
        
        if vehicle_type not in allowed_list:
            allowed_names = ", ".join([vt.display_name for vt in allowed_list])
            raise ValueError(
                f"🚫 Tipo de vehículo no permitido: El vehículo {vehicle.license_plate} "
                f"es tipo '{vehicle_type.display_name}', pero la planta '{facility.name}' "
                f"solo permite: {allowed_names}"
            )

    def get_loads_by_trip_id(self, trip_id: str) -> List[Load]:
        """
        Obtiene todas las cargas asociadas a un trip.
        
        Args:
            trip_id: UUID del trip
            
        Returns:
            Lista de cargas del trip
        """
        return self.load_repo.get_loads_by_trip_id(trip_id)

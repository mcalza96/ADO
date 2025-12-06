"""
LoadReceptionService - Maneja la recepción y cierre de cargas.

Responsabilidades:
- Registro de llegada a destino (gate in)
- Pesaje y control de calidad
- Cierre de viajes (trip completion)
- Validación de documentos de recepción
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from infrastructure.persistence.database_manager import DatabaseManager
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus


class LoadReceptionService:
    """
    Servicio especializado en recepción de cargas en destino.
    
    Gestiona la llegada del vehículo, pesaje, control de calidad
    y cierre administrativo del viaje.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)

    def register_arrival(
        self,
        load_id: int,
        weight_gross: float = None,
        ph: float = None,
        humidity: float = None,
        observation: str = None
    ) -> bool:
        """
        Registra la llegada de una carga al destino.
        
        Transición típica: EN_ROUTE_DESTINATION -> AT_DESTINATION
        
        Args:
            load_id: ID de la carga
            weight_gross: Peso bruto en báscula de entrada (toneladas)
            ph: pH del lodo (control de calidad)
            humidity: Humedad del lodo (%)
            observation: Observaciones del operador
            
        Returns:
            True si el registro fue exitoso
            
        Raises:
            ValueError: Si la carga no existe
            
        Note:
            Este método actualiza el modelo Load directamente.
            Para transición de estado completa, usar LoadStateService.transition_load()
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
        
        # Usar método del modelo para registrar llegada
        load.register_arrival(weight_gross, ph, humidity, observation)
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    def close_trip(self, load_id: int, data_dict: Dict[str, Any]) -> bool:
        """
        Cierra un viaje con todos los datos de recepción.
        
        Transición típica: AT_DESTINATION -> COMPLETED
        
        Args:
            load_id: ID de la carga
            data_dict: Diccionario con datos de cierre:
                - weight_net: Peso neto final (toneladas)
                - ticket_number: Número de ticket de pesaje
                - guide_number: Número de guía de transporte
                - quality_ph: pH del lodo
                - quality_humidity: Humedad del lodo (%)
                
        Returns:
            True si el cierre fue exitoso
            
        Raises:
            ValueError: Si faltan campos requeridos o la carga no existe
            
        Example:
            data = {
                'weight_net': 24.5,
                'ticket_number': 'TKT-2024-001',
                'guide_number': 'GDE-2024-001',
                'quality_ph': 7.2,
                'quality_humidity': 75.0
            }
            service.close_trip(load_id=123, data_dict=data)
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
        
        # Extraer campos requeridos
        weight_net = data_dict.get('weight_net')
        ticket = data_dict.get('ticket_number')
        guide = data_dict.get('guide_number')
        ph = data_dict.get('quality_ph')
        humidity = data_dict.get('quality_humidity')
        
        # Validar que todos los campos requeridos estén presentes
        if any(v is None for v in [weight_net, ticket, guide, ph, humidity]):
            raise ValueError("Missing required fields for closing trip")

        # Usar método del modelo para cerrar viaje
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

    # --- Query Methods ---
    
    def get_loads_at_destination(self, site_id: Optional[int] = None) -> List[Load]:
        """
        Obtiene cargas que están en destino esperando procesamiento.
        
        Args:
            site_id: Filtrar por sitio específico (opcional)
            
        Returns:
            Lista de cargas con estado AT_DESTINATION
        """
        loads = self.load_repo.get_by_status(LoadStatus.AT_DESTINATION.value)
        
        if site_id:
            loads = [l for l in loads if l.destination_site_id == site_id]
        
        return loads
    
    def get_loads_by_facility(self, facility_id: int) -> List[Load]:
        """
        Obtiene cargas asociadas a una planta de origen.
        
        Args:
            facility_id: ID de la planta
            
        Returns:
            Lista de cargas con ese origen
        """
        return self.load_repo.get_all_filtered(origin_facility_id=facility_id)

    def get_loads_by_status(self, status: str) -> List[Load]:
        """
        Obtiene cargas por estado específico.
        
        Args:
            status: Estado de la carga (string)
            
        Returns:
            Lista de cargas con ese estado
        """
        return self.load_repo.get_by_status(status)

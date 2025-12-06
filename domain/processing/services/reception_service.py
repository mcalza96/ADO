from typing import List, Optional
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.repositories.load_repository import LoadRepository

class TreatmentReceptionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)

    def get_pending_reception_loads(self, plant_id: int) -> List[Load]:
        """Loads that are 'Delivered' (Closed by Driver) at the Treatment Plant."""
        return self.load_repo.get_delivered_by_destination_type('TreatmentPlant', plant_id)

    def get_in_transit_loads_by_treatment_plant(self, plant_id: int) -> List[Load]:
        """
        Get loads in transit (EN_ROUTE_DESTINATION) heading to a treatment plant.
        
        Used by treatment reception to show incoming trucks.
        
        Args:
            plant_id: ID of the destination treatment plant
            
        Returns:
            List of loads in transit to the plant
        """
        return self.load_repo.get_in_transit_loads_by_treatment_plant(plant_id)

    def execute_reception(
        self, 
        load_id: int, 
        reception_time: datetime, 
        discharge_time: datetime, 
        ph: float, 
        humidity: float,
        observation: Optional[str] = None,
        arrival_ph: Optional[float] = None
    ) -> Load:
        """
        Complete reception at treatment plant: EN_ROUTE_DESTINATION -> COMPLETED.
        
        Captures quality verification (pH and humidity) at treatment plant reception.
        For treatment plants, reception completes the load cycle (unlike disposal
        where there's a subsequent field application step).
        
        Args:
            load_id: ID of the load to receive
            reception_time: Actual arrival time at plant
            discharge_time: Time of pit discharge
            ph: pH verification at reception (legacy, use arrival_ph)
            humidity: Humidity verification at reception
            observation: Optional quality observations
            arrival_ph: pH measured at arrival (new field for traceability)
            
        Returns:
            Updated Load entity
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
        
        # Aceptar tanto el nuevo status como el legacy
        valid_statuses = [LoadStatus.EN_ROUTE_DESTINATION.value, 'Delivered', 'InTransit', LoadStatus.AT_DESTINATION.value]
        if load.status not in valid_statuses:
            raise ValueError(f"Load must be in transit to execute reception. Current: {load.status}")
        
        # En tratamiento, la recepción completa el ciclo de la carga
        # (a diferencia de disposición donde después hay aplicación en campo)
        load.status = LoadStatus.COMPLETED.value
        load.arrival_time = reception_time
        
        # El arrival_ph es el pH medido al llegar, distinto del quality_ph de origen
        if arrival_ph is not None:
            load.arrival_ph = arrival_ph
        
        # Mantener quality_ph y quality_humidity como los valores de origen (despacho)
        # Solo actualizarlos si no existen
        if load.quality_ph is None:
            load.quality_ph = ph
        if load.quality_humidity is None:
            load.quality_humidity = humidity
            
        load.updated_at = datetime.now()
        
        # Guardar observaciones si las hay
        if observation:
            load.reception_observations = observation
        
        # Guardar datos adicionales en attributes para flexibilidad
        if not load.attributes:
            load.attributes = {}
        load.attributes['discharge_time'] = discharge_time.isoformat()
        load.attributes['ph_at_reception'] = arrival_ph or ph
        load.attributes['humidity_at_reception'] = humidity
        load.attributes['reception_timestamp'] = datetime.now().isoformat()
        load.attributes['completed_at'] = datetime.now().isoformat()
            
        return self.load_repo.update(load)

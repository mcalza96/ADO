from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class PickupRequestStatus(str, Enum):
    """Estado de la solicitud de retiro."""
    PENDING = "PENDING"           # Pendiente de programar
    PARTIALLY_SCHEDULED = "PARTIALLY_SCHEDULED"  # Algunas cargas programadas
    FULLY_SCHEDULED = "FULLY_SCHEDULED"  # Todas las cargas programadas
    IN_PROGRESS = "IN_PROGRESS"   # Cargas en ejecución
    COMPLETED = "COMPLETED"       # Todas las cargas completadas
    CANCELLED = "CANCELLED"       # Cancelada


@dataclass
class PickupRequest:
    """
    Solicitud de retiros del cliente o planta de tratamiento.
    
    Agrupa múltiples cargas (Load) que el cliente solicita para una misma
    planta y fecha. Permite especificar tipo de vehículo y cantidad de
    contenedores para AMPLIROLL.
    
    Ejemplo: "4 cargas de PTAS Bio bio (bateas), 2 cargas de PTAS Arauco 
              con 2 contenedores c/u, en la fecha x"
    
    Attributes:
        client_id: Cliente que solicita el retiro (None para solicitudes internas)
        facility_id: Planta de origen del residuo (cliente)
        treatment_plant_id: Planta de tratamiento de origen (solicitudes internas)
        requested_date: Fecha solicitada para los retiros
        vehicle_type: Tipo de vehículo requerido (BATEA/AMPLIROLL)
        load_quantity: Cantidad de retiros/cargas solicitadas
        containers_per_load: Contenedores por carga (solo AMPLIROLL, 1-2)
        notes: Observaciones del cliente
        status: Estado de la solicitud
    """
    id: Optional[int]
    client_id: Optional[int]  # None para solicitudes internas (planta de tratamiento)
    facility_id: Optional[int]  # Planta del cliente (origen externo)
    treatment_plant_id: Optional[int] = None  # Planta de tratamiento (origen interno)
    requested_date: date = None
    vehicle_type: str = "AMPLIROLL"  # BATEA o AMPLIROLL
    load_quantity: int = 1  # Cuántas cargas/retiros
    containers_per_load: Optional[int] = None  # Solo para AMPLIROLL (1-2)
    notes: Optional[str] = None
    status: str = PickupRequestStatus.PENDING.value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Campos para display (no persistidos)
    client_name: Optional[str] = None
    facility_name: Optional[str] = None
    treatment_plant_name: Optional[str] = None  # Nombre de planta de tratamiento
    scheduled_count: Optional[int] = None  # Cargas ya programadas
    
    @property
    def origin_name(self) -> str:
        """Nombre del origen (facility o treatment plant)."""
        return self.facility_name or self.treatment_plant_name or "N/A"
    
    @property
    def is_internal_request(self) -> bool:
        """Indica si es una solicitud interna (desde planta de tratamiento)."""
        return self.treatment_plant_id is not None and self.client_id is None
    
    @property
    def total_containers(self) -> int:
        """Total de contenedores en esta solicitud."""
        if self.vehicle_type == "AMPLIROLL" and self.containers_per_load:
            return self.load_quantity * self.containers_per_load
        return 0
    
    @property
    def is_fully_scheduled(self) -> bool:
        """Indica si todas las cargas han sido programadas."""
        return self.status == PickupRequestStatus.FULLY_SCHEDULED.value
    
    @property
    def pending_loads(self) -> int:
        """Cantidad de cargas pendientes de programar."""
        scheduled = self.scheduled_count or 0
        return max(0, self.load_quantity - scheduled)
    
    def update_status_from_loads(self, scheduled: int, completed: int, in_transit: int):
        """Actualiza el estado basándose en el estado de las cargas asociadas."""
        if completed >= self.load_quantity:
            self.status = PickupRequestStatus.COMPLETED.value
        elif in_transit > 0 or completed > 0:
            self.status = PickupRequestStatus.IN_PROGRESS.value
        elif scheduled >= self.load_quantity:
            self.status = PickupRequestStatus.FULLY_SCHEDULED.value
        elif scheduled > 0:
            self.status = PickupRequestStatus.PARTIALLY_SCHEDULED.value
        else:
            self.status = PickupRequestStatus.PENDING.value

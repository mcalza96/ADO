from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    origin_facility_id: int
    
    # Campos asignados por el planificador (nullable cuando status=REQUESTED)
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    destination_site_id: Optional[int] = None
    contractor_id: Optional[int] = None
    destination_plot_id: Optional[int] = None
    
    # Optional/Nullable fields
    manifest_code: Optional[str] = None
    container_id: Optional[int] = None
    batch_id: Optional[int] = None # Legacy/Compatibility
    treatment_batch_id: Optional[int] = None # Link to operational batch
    origin_treatment_plant_id: Optional[int] = None
    destination_treatment_plant_id: Optional[int] = None
    
    # Pickup Request - Solicitud del cliente
    pickup_request_id: Optional[int] = None  # Agrupa cargas de una misma solicitud
    vehicle_type_requested: Optional[str] = None  # BATEA o AMPLIROLL solicitado
    container_quantity: Optional[int] = None  # Cantidad de contenedores (AMPLIROLL: 1-2)
    
    # Operational Data
    material_class: Optional[str] = None
    ticket_number: Optional[str] = None  # Número de ticket de pesaje
    guide_number: Optional[str] = None  # Guía de despacho
    reception_observations: Optional[str] = None  # Observaciones en recepción
    quality_ph: Optional[float] = None  # pH de la carga (en origen/despacho)
    quality_humidity: Optional[float] = None  # Humedad de la carga (%)
    arrival_ph: Optional[float] = None  # pH medido al llegar a planta de tratamiento
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    weight_net: Optional[float] = None  # Alias for net_weight (backward compatibility)
    weight_gross_reception: Optional[float] = None  # Peso bruto en recepción
    disposal_time: Optional[datetime] = None  # Tiempo de disposición final
    
    # Status and Timing
    status: str = 'CREATED'
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
    # Flexible Attributes (JSONB-like storage)
    # Permite almacenar datos variables sin cambiar el schema:
    # Ejemplo: attributes = {'ph_inicial': 7.5, 'temperatura_llegada': 25.3, 'odometro_inicio': 145230}
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None

    def calculate_net_weight(self) -> None:
        """
        Updates the net_weight if gross_weight and tare_weight are present.
        """
        if self.gross_weight is not None and self.tare_weight is not None:
            self.net_weight = self.gross_weight - self.tare_weight

    def close_trip(
        self,
        weight_net: float,
        ticket_number: str,
        guide_number: str,
        ph: float,
        humidity: float
    ) -> None:
        """
        Cierra el viaje con los datos del despacho y cambia el estado a EN_ROUTE_DESTINATION.
        
        Este método es llamado por el conductor al confirmar el despacho.
        
        Args:
            weight_net: Peso neto de la carga (kg)
            ticket_number: Número de ticket de pesaje
            guide_number: Número de guía de transporte
            ph: pH de la carga
            humidity: Humedad de la carga (%)
        """
        self.weight_net = weight_net
        self.net_weight = weight_net  # Alias
        self.ticket_number = ticket_number
        self.guide_number = guide_number
        self.quality_ph = ph
        self.quality_humidity = humidity
        self.status = 'EN_ROUTE_DESTINATION'
        self.dispatch_time = datetime.now()
        self.updated_at = datetime.now()

    def register_arrival(
        self,
        weight_gross: Optional[float] = None,
        ph: Optional[float] = None,
        humidity: Optional[float] = None,
        observation: Optional[str] = None
    ) -> None:
        """
        Registra la llegada al destino.
        
        Este método es llamado por el operario de báscula/recepción.
        
        Args:
            weight_gross: Peso bruto en báscula de destino (kg)
            ph: pH medido en recepción
            humidity: Humedad medida en recepción (%)
            observation: Observaciones de calidad
        """
        if weight_gross is not None:
            self.weight_gross_reception = weight_gross
        if ph is not None:
            self.quality_ph = ph
        if humidity is not None:
            self.quality_humidity = humidity
        if observation:
            self.reception_observations = observation
        
        self.arrival_time = datetime.now()
        self.status = 'AT_DESTINATION'
        self.updated_at = datetime.now()


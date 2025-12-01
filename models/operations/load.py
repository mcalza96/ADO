from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Load:
    id: Optional[int]
    origin_facility_id: Optional[int] = None # Client Facility
    origin_treatment_plant_id: Optional[int] = None # Treatment Plant (Outbound)
    
    # Optional fields for Request phase
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    destination_site_id: Optional[int] = None
    batch_id: Optional[int] = None
    container_quantity: Optional[int] = None # For AmpliRoll trucks
    
    # Execution details
    ticket_number: Optional[str] = None
    guide_number: Optional[str] = None
    weight_gross: Optional[float] = None
    weight_tare: Optional[float] = None
    weight_net: Optional[float] = None
    weight_gross_reception: Optional[float] = None # Peso bruto en recepción (TTO-03)
    reception_observations: Optional[str] = None  # Observaciones de calidad en recepción
    
    status: str = 'Requested'
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    dispatch_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    
    # Disposal Traceability
    disposal_time: Optional[datetime] = None
    disposal_coordinates: Optional[str] = None
    
    # Hybrid Logistics
    destination_facility_id: Optional[int] = None # For Client -> Client transfers (rare)
    destination_treatment_plant_id: Optional[int] = None # For Client -> Plant
    
    # Treatment Reception Data
    reception_time: Optional[datetime] = None
    discharge_time: Optional[datetime] = None
    quality_ph: Optional[float] = None
    quality_humidity: Optional[float] = None
    
    # DS4 Container Logistics
    container_1_id: Optional[int] = None
    container_2_id: Optional[int] = None
    batch_1_id: Optional[int] = None # Link to TreatmentBatch (Quality Data)
    batch_2_id: Optional[int] = None # Link to TreatmentBatch (Quality Data)
    
    transport_company_id: Optional[int] = None
    treatment_facility_id: Optional[int] = None # If intermediate treatment occurred (Legacy/Reference)
    
    # Audit
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    created_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Sync Support
    sync_status: str = 'PENDING' # 'SYNCED', 'PENDING', 'ERROR'
    last_updated_local: Optional[datetime] = None
    
    # --- Business Logic Methods ---
    def register_arrival(self, weight_gross: float = None, ph: float = None, humidity: float = None, observation: str = None) -> None:
        """
        Registra la llegada física de la carga a portería/pesaje (TTO-03).
        Transiciona de InTransit -> Arrived.
        
        Args:
            weight_gross: Peso bruto registrado en báscula (kg) (Opcional en llegada, obligatorio en cierre)
            ph: pH registrado (Opcional)
            humidity: Humedad registrada (%) (Opcional)
            observation: Observaciones opcionales de calidad
            
        Raises:
            ValueError: Si la carga no está en estado InTransit
        """
        # Validation: Verify current state
        if self.status != 'InTransit':
            raise ValueError(f"Solo se puede recepcionar cargas InTransit. Estado actual: {self.status}")
        
        # State Transition: Update status and arrival properties
        self.status = 'Arrived'
        self.arrival_time = datetime.now()
        
        # Optional updates at arrival (can be updated later at close_trip)
        if weight_gross is not None:
            self.weight_gross_reception = weight_gross
        if ph is not None:
            self.quality_ph = ph
        if humidity is not None:
            self.quality_humidity = humidity
        if observation is not None:
            self.reception_observations = observation
    
    def close_trip(self, weight_net: float, ticket_number: str, guide_number: str, ph: float, humidity: float) -> None:
        """
        Cierra el viaje en destino.
        Transiciona de Arrived -> Delivered.
        
        Args:
            weight_net: Peso neto final
            ticket_number: Número de ticket de pesaje
            guide_number: Número de guía de despacho
            ph: pH final
            humidity: Humedad final
            
        Raises:
            ValueError: Si la carga no está en estado Arrived o si los datos de calidad están fuera de rango
        """
        # Validation: Verify current state
        if self.status != 'Arrived':
            raise ValueError(f"Solo se puede cerrar cargas Arrived. Estado actual: {self.status}")
        
        # Validation: Quality parameters must be within acceptable ranges
        if ph < 5.0 or ph > 9.0:
            raise ValueError(f"pH fuera de rango válido (5-9). Valor recibido: {ph}")
        
        if humidity < 0.0 or humidity > 100.0:
            raise ValueError(f"Humedad fuera de rango válido (0-100%). Valor recibido: {humidity}")
            
        self.status = 'Delivered'
        self.weight_net = weight_net
        self.ticket_number = ticket_number
        self.guide_number = guide_number
        self.quality_ph = ph
        self.quality_humidity = humidity
        self.updated_at = datetime.now()

    def complete_disposal(self, coordinates: str, treatment_facility_id: Optional[int] = None) -> None:
        """
        Execute disposal of the load, transitioning from Delivered to Disposed.
        Note: This might be deprecated or moved to a separate service/flow depending on 'Delivered' being the final state for DispatchService.
        Keeping for backward compatibility or future disposal flow.
        """
        # Validation: Verify current state
        if self.status != 'Delivered':
             # Allow Arrived for backward compatibility if needed, but prefer Delivered
            if self.status != 'Arrived':
                raise ValueError(f"Load must be Delivered (or Arrived) to execute disposal. Current: {self.status}")
        
        # State Transition: Update status and disposal properties
        self.status = 'Disposed'
        self.disposal_time = datetime.now()
        self.disposal_coordinates = coordinates
        if treatment_facility_id is not None:
            self.treatment_facility_id = treatment_facility_id

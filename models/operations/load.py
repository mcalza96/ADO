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
    def complete_disposal(self, coordinates: str, treatment_facility_id: Optional[int] = None) -> None:
        """
        Execute disposal of the load, transitioning from PendingDisposal to Disposed.
        
        Args:
            coordinates: GPS coordinates of the disposal location
            treatment_facility_id: Optional ID of the treatment facility
            
        Raises:
            ValueError: If load is not in PendingDisposal status
        """
        # Validation: Verify current state
        if self.status != 'PendingDisposal':
            raise ValueError(f"Load must be PendingDisposal to execute disposal. Current: {self.status}")
        
        # State Transition: Update status and disposal properties
        self.status = 'Disposed'
        self.disposal_time = datetime.now()
        self.disposal_coordinates = coordinates
        if treatment_facility_id is not None:
            self.treatment_facility_id = treatment_facility_id

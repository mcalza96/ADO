from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- DTOs ---
class TreatmentReceptionDTO(BaseModel):
    """Data for registering load arrival at treatment plant."""
    load_id: int = Field(gt=0)
    reception_time: datetime
    discharge_time: datetime
    ph: float = Field(ge=0, le=14)
    humidity: float = Field(ge=0, le=100)
    observation: Optional[str] = Field(None, max_length=500)
    arrival_ph: Optional[float] = Field(None, ge=0, le=14)

# --- Application Service ---
class TreatmentApplicationService:
    """
    Application Service for Treatment Operations.
    Orchestrates Reception at Treatment Plants.
    """
    def __init__(self, reception_service):
        self.reception_service = reception_service

    def get_incoming_loads(self, plant_id: int) -> List[Any]:
        """Get loads in transit to a specific treatment plant."""
        return self.reception_service.get_in_transit_loads_by_treatment_plant(plant_id)

    def execute_reception(self, dto: TreatmentReceptionDTO) -> None:
        """Execute reception at treatment plant (Gate In + Completion)."""
        self.reception_service.execute_reception(
            load_id=dto.load_id,
            reception_time=dto.reception_time,
            discharge_time=dto.discharge_time,
            ph=dto.ph,
            humidity=dto.humidity,
            observation=dto.observation,
            arrival_ph=dto.arrival_ph
        )

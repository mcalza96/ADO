from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- DTOs ---
class DisposalReceptionDTO(BaseModel):
    """Data for registering load arrival at disposal site."""
    load_id: int = Field(gt=0)
    ph: float = Field(ge=0, le=14)
    observation: Optional[str] = Field(None, max_length=500)

class DisposalExecutionDTO(BaseModel):
    """Data for executing disposal (incorporation) in a plot."""
    load_id: int = Field(gt=0)
    plot_id: int = Field(gt=0)
    observation: Optional[str] = Field(None, max_length=500)

# --- Application Service ---
class DisposalApplicationService:
    """
    Application Service for Disposal Operations.
    Orchestrates Reception and Field Incorporation.
    """
    def __init__(self, disposal_service):
        self.disposal_service = disposal_service

    def get_incoming_loads(self, site_id: int) -> List[Any]:
        """Get loads in transit to a specific site."""
        return self.disposal_service.get_in_transit_loads_by_destination_site(site_id)

    def get_pending_disposal_loads(self, site_id: int) -> List[Any]:
        """Get loads arrived at site, waiting for disposal."""
        return self.disposal_service.get_pending_disposal_loads(site_id)

    def get_site_plots(self, site_id: int) -> List[Any]:
        """Get active plots for a site."""
        return self.disposal_service.get_plots_by_site(site_id)

    def register_arrival(self, dto: DisposalReceptionDTO) -> None:
        """Register load arrival at site (Gate In)."""
        self.disposal_service.register_arrival(
            load_id=dto.load_id,
            ph=dto.ph,
            observation=dto.observation
        )

    def execute_disposal(self, dto: DisposalExecutionDTO) -> None:
        """Execute disposal (incorporation) of load into a plot."""
        self.disposal_service.execute_disposal(
            load_id=dto.load_id,
            plot_id=dto.plot_id,
            observation=dto.observation
        )

"""
Pydantic DTOs for Agronomy/Disposal Operations.

Site management, nitrogen tracking, field operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ==================== REQUEST DTOs ====================

class SiteCreateRequestDTO(BaseModel):
    """Request to create a new site."""
    name: str = Field(min_length=1, max_length=200)
    region: str = Field(min_length=1, max_length=100)
    commune: str = Field(min_length=1, max_length=100)
    total_area_ha: float = Field(gt=0, le=10000, description="Total area in hectares")
    agricultural_area_ha: Optional[float] = Field(None, ge=0)
    client_id: Optional[int] = Field(None, gt=0)
    is_active: bool = True
    
    @field_validator('agricultural_area_ha')
    @classmethod
    def validate_agricultural_area(cls, v, info):
        if v is not None and 'total_area_ha' in info.data:
            if v > info.data['total_area_ha']:
                raise ValueError("Agricultural area cannot exceed total area")
        return v


class PlotCreateRequestDTO(BaseModel):
    """Request to create a new plot within a site."""
    site_id: int = Field(gt=0)
    plot_number: str = Field(min_length=1, max_length=50)
    area_ha: float = Field(gt=0, le=1000)
    soil_type: Optional[str] = Field(None, max_length=100)
    current_crop: Optional[str] = Field(None, max_length=100)
    slope_percent: Optional[float] = Field(None, ge=0, le=100)
    is_active: bool = True


class SiteEventRequestDTO(BaseModel):
    """Request to register a site event (preparation, closure, etc.)."""
    site_id: int = Field(gt=0)
    event_type: str = Field(min_length=1, max_length=50)  # 'Preparation', 'Closure', 'Inspection'
    event_date: datetime
    description: Optional[str] = Field(None, max_length=500)
    performed_by: Optional[str] = Field(None, max_length=100)


class SoilSampleRequestDTO(BaseModel):
    """Request to register a soil sample analysis."""
    plot_id: int = Field(gt=0)
    sample_date: date
    nitrogen_ppm: Optional[float] = Field(None, ge=0)
    phosphorus_ppm: Optional[float] = Field(None, ge=0)
    potassium_ppm: Optional[float] = Field(None, ge=0)
    ph: Optional[float] = Field(None, ge=4.0, le=10.0)
    organic_matter_percent: Optional[float] = Field(None, ge=0, le=100)
    lab_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class MachineryLogRequestDTO(BaseModel):
    """Request to log heavy machinery work."""
    machine_id: int = Field(gt=0)
    site_id: int = Field(gt=0)
    operator_name: str = Field(min_length=1, max_length=100)
    start_time: datetime
    end_time: datetime
    horometer_start: float = Field(ge=0)
    horometer_end: float = Field(ge=0)
    work_type: str = Field(min_length=1, max_length=100)  # 'Incorporation', 'Leveling', 'Tilling'
    area_worked_ha: Optional[float] = Field(None, gt=0)
    fuel_consumed_liters: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('horometer_end')
    @classmethod
    def validate_horometer(cls, v, info):
        if 'horometer_start' in info.data and v <= info.data['horometer_start']:
            raise ValueError("End horometer must be greater than start horometer")
        return v
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("End time must be after start time")
        return v


class NitrogenApplicationRequestDTO(BaseModel):
    """Request to register nitrogen application (automatic from dispatch)."""
    site_id: int = Field(gt=0)
    load_id: int = Field(gt=0)
    batch_id: int = Field(gt=0)
    weight_net: float = Field(gt=0)
    application_date: date


# ==================== RESPONSE DTOs ====================

class SiteResponseDTO(BaseModel):
    """Response with site information."""
    id: int
    name: str
    region: str
    commune: str
    total_area_ha: float
    agricultural_area_ha: Optional[float]
    nitrogen_limit_kg: float
    nitrogen_applied_kg: float
    nitrogen_remaining_kg: float
    capacity_percent: float
    status: str  # 'Active', 'Closed', 'Inactive'
    client_name: Optional[str]
    last_application_date: Optional[date]
    
    class Config:
        from_attributes = True


class PlotResponseDTO(BaseModel):
    """Response with plot information."""
    id: int
    site_id: int
    site_name: str
    plot_number: str
    area_ha: float
    soil_type: Optional[str]
    current_crop: Optional[str]
    slope_percent: Optional[float]
    nitrogen_applied_kg: float
    last_sample_date: Optional[date]
    is_active: bool


class SiteEventResponseDTO(BaseModel):
    """Response with site event details."""
    id: int
    site_id: int
    site_name: str
    event_type: str
    event_date: datetime
    description: Optional[str]
    performed_by: Optional[str]
    created_at: datetime


class NitrogenBalanceDTO(BaseModel):
    """
    Response with nitrogen balance for a site.
    Used for compliance and decision-making.
    """
    site_id: int
    site_name: str
    total_area_ha: float
    application_rate_kg_ha_year: float  # Regulatory limit
    annual_limit_kg: float
    current_year_applied_kg: float
    previous_year_applied_kg: float
    remaining_capacity_kg: float
    capacity_percent_used: float
    days_until_reset: int
    can_accept_load: bool
    recommended_max_load_kg: float
    applications_this_year: int
    last_application_date: Optional[date]


class MachineryLogResponseDTO(BaseModel):
    """Response with machinery log details."""
    id: int
    machine_id: int
    machine_name: str
    site_id: int
    site_name: str
    operator_name: str
    start_time: datetime
    end_time: datetime
    duration_hours: float
    horometer_start: float
    horometer_end: float
    horometer_delta: float
    work_type: str
    area_worked_ha: Optional[float]
    fuel_consumed_liters: Optional[float]
    notes: Optional[str]


class SiteAgronomicSummaryDTO(BaseModel):
    """
    Comprehensive agronomic summary for a site.
    Used in planning and reporting views.
    """
    site_id: int
    site_name: str
    total_area_ha: float
    agricultural_area_ha: float
    
    # Nitrogen
    nitrogen_limit_kg: float
    nitrogen_applied_kg: float
    nitrogen_remaining_kg: float
    
    # Applications
    total_applications: int
    total_tonnage_applied: float
    average_application_rate: float  # kg N/ha
    
    # Timeline
    first_application_date: Optional[date]
    last_application_date: Optional[date]
    days_since_last_application: Optional[int]
    
    # Status
    status: str
    can_receive_more: bool
    estimated_months_remaining: Optional[float]
    
    # Plots
    total_plots: int
    active_plots: int


# ==================== QUERY DTOs ====================

class SiteFilterDTO(BaseModel):
    """DTO for filtering sites."""
    region: Optional[str] = None
    commune: Optional[str] = None
    client_id: Optional[int] = None
    is_active: Optional[bool] = None
    has_capacity: Optional[bool] = None  # Filter only sites with remaining nitrogen capacity
    min_area_ha: Optional[float] = None
    max_area_ha: Optional[float] = None


class NitrogenApplicationFilterDTO(BaseModel):
    """DTO for filtering nitrogen applications."""
    site_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    min_kg: Optional[float] = None
    max_kg: Optional[float] = None


# ==================== VALIDATION DTOs ====================

class SiteCapacityCheckRequestDTO(BaseModel):
    """Request to check if site can accept a load."""
    site_id: int = Field(gt=0)
    planned_nitrogen_kg: float = Field(gt=0)


class SiteCapacityCheckResponseDTO(BaseModel):
    """Response from site capacity check."""
    can_accept: bool
    current_applied_kg: float
    limit_kg: float
    remaining_kg: float
    after_application_kg: float
    after_application_percent: float
    compliance_issues: list[str] = []
    warnings: list[str] = []


# ==================== EXAMPLE USAGE ====================

"""
Example: Creating a Site with Pydantic Validation
--------------------------------------------------

```python
import streamlit as st
from domain.agronomy.dtos import SiteCreateRequestDTO, SiteResponseDTO

def create_site_form():
    st.subheader("Create New Site")
    
    name = st.text_input("Site Name")
    region = st.selectbox("Region", regions)
    commune = st.selectbox("Commune", communes)
    total_area = st.number_input("Total Area (ha)", min_value=0.1)
    agricultural_area = st.number_input("Agricultural Area (ha)", min_value=0.0)
    
    if st.button("Create Site"):
        try:
            # Pydantic validates automatically
            request = SiteCreateRequestDTO(
                name=name,
                region=region,
                commune=commune,
                total_area_ha=total_area,
                agricultural_area_ha=agricultural_area,
                is_active=True
            )
            
            # Will raise ValidationError if agricultural_area > total_area
            response: SiteResponseDTO = (
                container.agronomy_app_service.create_site(request)
            )
            
            st.success(f"Site '{response.name}' created with ID {response.id}")
            st.info(f"Nitrogen limit: {response.nitrogen_limit_kg:.0f} kg N/year")
            
        except ValidationError as e:
            st.error(f"Validation error: {e}")
```

Example: Machinery Log with Fraud Prevention
---------------------------------------------

```python
from domain.agronomy.dtos import MachineryLogRequestDTO

def log_machinery_work():
    # Form inputs...
    
    try:
        request = MachineryLogRequestDTO(
            machine_id=machine_id,
            site_id=site_id,
            operator_name=operator,
            start_time=start_dt,
            end_time=end_dt,
            horometer_start=start_horometer,
            horometer_end=end_horometer,  # Pydantic ensures end > start
            work_type=work_type
        )
        
        # This will fail at Pydantic level if:
        # - end_time <= start_time
        # - horometer_end <= horometer_start
        
        response = container.agronomy_app_service.log_machinery_work(request)
        st.success("Machinery work logged")
        
    except ValidationError as e:
        st.error(f"Invalid data: {e}")
```
"""

"""
Pydantic DTOs for Logistics/Dispatch Operations.

These DTOs provide:
- Type safety
- Automatic validation
- Clear API contracts between UI and Application Services
- Self-documenting code

Usage in UI:
    from domain.logistics.dtos import DispatchRequestDTO
    
    request = DispatchRequestDTO(
        batch_id=batch_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        destination_site_id=site_id,
        weight_net=weight
    )
    
    response = container.dispatch_app_service.execute(request)
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ==================== REQUEST DTOs (UI -> Application Service) ====================

class DispatchRequestDTO(BaseModel):
    """
    Request to dispatch a truck with biosolids.
    
    Validations:
    - weight_net must be positive
    - All IDs must be positive integers
    """
    batch_id: int = Field(gt=0, description="ID of the treatment batch")
    driver_id: int = Field(gt=0, description="ID of the assigned driver")
    vehicle_id: int = Field(gt=0, description="ID of the assigned vehicle")
    destination_site_id: int = Field(gt=0, description="ID of the destination site")
    origin_facility_id: int = Field(gt=0, description="ID of the origin facility")
    weight_net: float = Field(gt=0, le=50000, description="Net weight in kg (max 50 tons)")
    guide_number: Optional[str] = Field(None, max_length=50, description="Transport guide number")
    container_id: Optional[int] = Field(None, gt=0, description="Container ID if applicable")
    scheduled_date: Optional[datetime] = Field(None, description="Scheduled dispatch datetime")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": 123,
                "driver_id": 45,
                "vehicle_id": 67,
                "destination_site_id": 89,
                "origin_facility_id": 1,
                "weight_net": 15000.0,
                "guide_number": "GTR-2024-001",
                "container_id": 10
            }
        }


class ReceptionRequestDTO(BaseModel):
    """
    Request to register arrival at destination (Gate In).
    
    Validations:
    - pH must be between 4.0 and 10.0
    - Humidity must be between 0 and 100
    """
    load_id: int = Field(gt=0)
    arrival_time: datetime
    weight_gross: Optional[float] = Field(None, gt=0, le=50000, description="Gross weight at arrival (kg)")
    ph: Optional[float] = Field(None, ge=4.0, le=10.0, description="pH value")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity percentage")
    observation: Optional[str] = Field(None, max_length=500)
    
    @field_validator('arrival_time')
    @classmethod
    def validate_arrival_not_future(cls, v):
        if v > datetime.now():
            raise ValueError("Arrival time cannot be in the future")
        return v


class LoadScheduleRequestDTO(BaseModel):
    """
    Request to schedule a load for future dispatch.
    """
    load_id: int = Field(gt=0)
    driver_id: int = Field(gt=0)
    vehicle_id: int = Field(gt=0)
    scheduled_date: datetime
    site_id: Optional[int] = Field(None, gt=0)
    treatment_plant_id: Optional[int] = Field(None, gt=0)
    container_quantity: Optional[int] = Field(None, ge=1, le=100)
    
    @field_validator('scheduled_date')
    @classmethod
    def validate_schedule_not_past(cls, v):
        if v < datetime.now():
            raise ValueError("Scheduled date cannot be in the past")
        return v


class TripStartRequestDTO(BaseModel):
    """Request to start a trip (Gate Out)."""
    load_id: int = Field(gt=0)
    actual_departure_time: Optional[datetime] = None


class TripCloseRequestDTO(BaseModel):
    """
    Request to close a completed trip.
    
    Includes all final data collected during the trip.
    """
    load_id: int = Field(gt=0)
    discharge_time: Optional[datetime] = None
    incorporation_time: Optional[datetime] = None
    equipment_used: Optional[str] = Field(None, max_length=200)
    operator_name: Optional[str] = Field(None, max_length=100)
    final_observation: Optional[str] = Field(None, max_length=500)
    quality_ph: Optional[float] = Field(None, ge=4.0, le=10.0)
    quality_humidity: Optional[float] = Field(None, ge=0, le=100)


# ==================== RESPONSE DTOs (Application Service -> UI) ====================

class DispatchResponseDTO(BaseModel):
    """
    Response after dispatch operation.
    Contains all info needed by UI to display result.
    """
    success: bool
    load_id: Optional[int] = None
    manifest_code: Optional[str] = None
    manifest_path: Optional[str] = None
    nitrogen_applied_kg: Optional[float] = None
    estimated_arrival: Optional[datetime] = None
    error_message: Optional[str] = None
    validation_warnings: list[str] = []


class LoadStatusResponseDTO(BaseModel):
    """Response with detailed load status information."""
    load_id: int
    status: str
    manifest_code: Optional[str]
    driver_name: Optional[str]
    vehicle_plate: Optional[str]
    destination: Optional[str]
    weight_net: Optional[float]
    dispatch_time: Optional[datetime]
    arrival_time: Optional[datetime]
    current_location: Optional[str]
    time_in_current_status: Optional[int]  # minutes
    can_transition_to: list[str] = []  # Possible next states


class SiteCapacityResponseDTO(BaseModel):
    """
    Response with site capacity information.
    Useful for validation before dispatch.
    """
    site_id: int
    site_name: str
    total_area_ha: float
    nitrogen_limit_kg: float
    nitrogen_applied_kg: float
    nitrogen_remaining_kg: float
    capacity_percent_used: float
    can_accept_more: bool
    status: str  # 'Available', 'Near Limit', 'At Capacity', 'Closed'
    next_available_date: Optional[date] = None


class LoadTimelineItemDTO(BaseModel):
    """Single timeline item for a load."""
    timestamp: datetime
    status: str
    user_name: Optional[str]
    notes: Optional[str]
    duration_in_status: Optional[int]  # minutes


class LoadTimelineResponseDTO(BaseModel):
    """Complete timeline for a load."""
    load_id: int
    manifest_code: str
    current_status: str
    timeline: list[LoadTimelineItemDTO]
    total_elapsed_time: int  # minutes from creation to now


# ==================== QUERY DTOs (for filtering/searching) ====================

class LoadFilterDTO(BaseModel):
    """
    DTO for filtering loads in queries.
    All fields optional - only specified fields are used for filtering.
    """
    status: Optional[str] = None
    facility_id: Optional[int] = None
    site_id: Optional[int] = None
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    batch_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    manifest_code: Optional[str] = None


class LoadSummaryDTO(BaseModel):
    """
    Lightweight DTO for load listings.
    Contains only essential fields for tables/lists.
    """
    id: int
    manifest_code: str
    status: str
    driver_name: str
    vehicle_plate: str
    destination_name: str
    weight_net: float
    dispatch_time: Optional[datetime]
    eta: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allows creation from ORM models


class DashboardMetricsDTO(BaseModel):
    """Aggregated metrics for dashboard display."""
    total_loads_today: int
    loads_in_transit: int
    loads_completed: int
    loads_pending: int
    total_tonnage_today: float
    average_trip_duration_minutes: Optional[float]
    alerts: list[str] = []


# ==================== VALIDATION DTOs ====================

class ComplianceCheckRequestDTO(BaseModel):
    """Request to check if dispatch complies with regulations."""
    batch_id: int = Field(gt=0)
    site_id: int = Field(gt=0)
    planned_tonnage: float = Field(gt=0)


class ComplianceCheckResponseDTO(BaseModel):
    """Response from compliance validation."""
    is_compliant: bool
    nitrogen_to_add_kg: float
    site_nitrogen_remaining_kg: float
    site_capacity_percent_after: float
    violations: list[str] = []
    warnings: list[str] = []


# ==================== UPDATE DTOs ====================

class LoadAttributesUpdateDTO(BaseModel):
    """
    DTO for updating load attributes (JSONB field).
    Used to save checkpoint data before state transitions.
    """
    load_id: int = Field(gt=0)
    attributes: dict  # Flexible key-value pairs
    
    class Config:
        json_schema_extra = {
            "example": {
                "load_id": 123,
                "attributes": {
                    "gps_coordinates": {"lat": -33.4372, "lon": -70.6506},
                    "temperature": 22.5,
                    "driver_notes": "Traffic delay on highway"
                }
            }
        }


class LoadTransitionRequestDTO(BaseModel):
    """
    Request to transition a load to a new status.
    Includes validation checkpoint data.
    """
    load_id: int = Field(gt=0)
    new_status: str = Field(min_length=1)
    user_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)
    checkpoint_data: Optional[dict] = None  # Required verifiers for this transition


class DispatchExecutionDTO(BaseModel):
    """
    Data required to execute a dispatch (Gate Out).
    """
    load_id: int = Field(gt=0, description="ID of the load being dispatched")
    ticket_number: str = Field(min_length=1, description="Weighing ticket number")
    guide_number: str = Field(min_length=1, description="Transport guide number")
    weight_net: float = Field(gt=0, le=50000, description="Net weight in kg")
    quality_ph: float = Field(ge=0, le=14, description="pH value")
    quality_humidity: float = Field(ge=0, le=100, description="Humidity percentage")
    
    # Optional container tracking fields (for treatment plants)
    container_1_id: Optional[int] = Field(None, description="ID of first container record")
    container_2_id: Optional[int] = Field(None, description="ID of second container record")


class PickupRequestDTO(BaseModel):
    """
    Data required to create a pickup request.
    """
    facility_id: int = Field(gt=0, description="ID of the origin facility")
    requested_date: datetime = Field(description="Date requested for pickup")
    weight_estimated: Optional[float] = Field(None, gt=0, description="Estimated weight in kg")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


# ==================== EXAMPLE USAGE ====================

"""
Example: Using DTOs in Streamlit UI
------------------------------------

```python
import streamlit as st
from domain.logistics.dtos import DispatchRequestDTO, DispatchResponseDTO

def dispatch_form():
    st.subheader("Dispatch Truck")
    
    # Collect form data
    batch_id = st.selectbox("Batch", batches, format_func=lambda x: x.code)
    driver_id = st.selectbox("Driver", drivers, format_func=lambda x: x.name)
    vehicle_id = st.selectbox("Vehicle", vehicles, format_func=lambda x: x.plate)
    site_id = st.selectbox("Site", sites, format_func=lambda x: x.name)
    weight = st.number_input("Weight (kg)", min_value=0.0, max_value=50000.0)
    
    if st.button("Dispatch"):
        try:
            # Create validated DTO
            request = DispatchRequestDTO(
                batch_id=batch_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                destination_site_id=site_id,
                origin_facility_id=st.session_state.facility_id,
                weight_net=weight
            )
            
            # Call application service
            response: DispatchResponseDTO = (
                container.dispatch_app_service.execute_dispatch(request)
            )
            
            # Display result
            if response.success:
                st.success(f"✅ Load {response.manifest_code} dispatched!")
                st.info(f"Nitrogen applied: {response.nitrogen_applied_kg:.1f} kg N")
                
                if response.manifest_path:
                    st.download_button(
                        "📄 Download Manifest",
                        data=open(response.manifest_path, 'rb'),
                        file_name=f"{response.manifest_code}.pdf"
                    )
            else:
                st.error(f"❌ {response.error_message}")
                
                for warning in response.validation_warnings:
                    st.warning(f"⚠️ {warning}")
                    
        except Exception as e:
            st.error(f"Validation error: {str(e)}")
```

Example: Application Service using DTOs
----------------------------------------

```python
from domain.logistics.dtos import DispatchRequestDTO, DispatchResponseDTO

class DispatchApplicationService:
    def execute_dispatch(self, request: DispatchRequestDTO) -> DispatchResponseDTO:
        try:
            # Request is already validated by Pydantic!
            # No need to check if weight > 0, IDs are positive, etc.
            
            # Business logic
            load = self.logistics_service.dispatch_truck(
                batch_id=request.batch_id,
                driver_id=request.driver_id,
                vehicle_id=request.vehicle_id,
                destination_site_id=request.destination_site_id,
                origin_facility_id=request.origin_facility_id,
                weight_net=request.weight_net,
                guide_number=request.guide_number,
                container_id=request.container_id
            )
            
            manifest = self.manifest_service.generate_manifest(load.id)
            agronomics = self.compliance_service.calculate_agronomics(
                request.batch_id, request.weight_net
            )
            
            return DispatchResponseDTO(
                success=True,
                load_id=load.id,
                manifest_code=load.manifest_code,
                manifest_path=manifest.path,
                nitrogen_applied_kg=agronomics['total_n_kg']
            )
            
        except ComplianceViolationError as e:
            return DispatchResponseDTO(
                success=False,
                error_message=str(e)
            )
```
"""

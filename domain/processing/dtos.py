"""
Pydantic DTOs for Processing/Treatment Operations.

Batch management, treatment plant operations, quality control.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ==================== REQUEST DTOs ====================

class BatchCreateRequestDTO(BaseModel):
    """Request to create a new treatment batch."""
    treatment_plant_id: int = Field(gt=0)
    source_type: str = Field(min_length=1, max_length=50)  # 'Municipal', 'Industrial'
    initial_volume_m3: float = Field(gt=0, le=10000)
    initial_solids_percent: Optional[float] = Field(None, ge=0, le=100)
    treatment_start_date: datetime
    operator_name: Optional[str] = Field(None, max_length=100)


class BatchUpdateRequestDTO(BaseModel):
    """Request to update batch status/measurements."""
    batch_id: int = Field(gt=0)
    current_volume_m3: Optional[float] = Field(None, gt=0)
    current_solids_percent: Optional[float] = Field(None, ge=0, le=100)
    ph: Optional[float] = Field(None, ge=4.0, le=10.0)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    nitrogen_percent: Optional[float] = Field(None, ge=0, le=20)
    phosphorus_percent: Optional[float] = Field(None, ge=0, le=20)
    biosolid_class: Optional[str] = Field(None, pattern=r'^[AB]$')
    status: Optional[str] = None  # 'Processing', 'Curing', 'Ready', 'Depleted'


class StockReservationRequestDTO(BaseModel):
    """Request to reserve stock from a batch."""
    batch_id: int = Field(gt=0)
    weight_kg: float = Field(gt=0)
    reserved_by: str = Field(min_length=1, max_length=100)
    reservation_date: Optional[datetime] = None


class TreatmentReceptionRequestDTO(BaseModel):
    """Request to register reception of biosolids at treatment plant."""
    load_id: int = Field(gt=0)
    reception_time: datetime
    discharge_time: datetime
    quality_ph: float = Field(ge=4.0, le=10.0)
    quality_humidity: float = Field(ge=0, le=100)
    quality_notes: Optional[str] = Field(None, max_length=500)
    operator_name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('discharge_time')
    @classmethod
    def validate_discharge_after_reception(cls, v, info):
        if 'reception_time' in info.data and v < info.data['reception_time']:
            raise ValueError("Discharge time must be after reception time")
        return v


class FacilityCreateRequestDTO(BaseModel):
    """Request to create a new facility."""
    name: str = Field(min_length=1, max_length=200)
    facility_type: str = Field(min_length=1, max_length=50)  # 'Treatment Plant', 'Transfer Station'
    region: str = Field(min_length=1, max_length=100)
    commune: str = Field(min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=300)
    capacity_m3_day: Optional[float] = Field(None, gt=0)
    is_active: bool = True


# ==================== RESPONSE DTOs ====================

class BatchResponseDTO(BaseModel):
    """Response with batch information."""
    id: int
    code: str
    treatment_plant_name: str
    source_type: str
    initial_volume_m3: float
    current_volume_m3: float
    reserved_volume_m3: float
    available_volume_m3: float
    current_solids_percent: Optional[float]
    ph: Optional[float]
    humidity: Optional[float]
    nitrogen_percent: Optional[float]
    phosphorus_percent: Optional[float]
    biosolid_class: Optional[str]
    status: str
    treatment_start_date: datetime
    last_updated: datetime
    days_in_treatment: int
    
    class Config:
        from_attributes = True


class BatchStockSummaryDTO(BaseModel):
    """Summary of batch stock availability."""
    batch_id: int
    batch_code: str
    total_volume_m3: float
    reserved_volume_m3: float
    dispatched_volume_m3: float
    available_volume_m3: float
    available_percent: float
    can_dispatch: bool
    minimum_reserve_m3: float
    status: str


class TreatmentPlantResponseDTO(BaseModel):
    """Response with treatment plant information."""
    id: int
    name: str
    facility_type: str
    region: str
    commune: str
    capacity_m3_day: Optional[float]
    active_batches: int
    total_available_volume_m3: float
    is_active: bool


class FacilityResponseDTO(BaseModel):
    """Response with facility information."""
    id: int
    name: str
    facility_type: str
    region: str
    commune: str
    address: Optional[str]
    is_active: bool
    total_loads_processed: Optional[int]
    average_daily_volume: Optional[float]


class QualityControlResultDTO(BaseModel):
    """Quality control test results for a batch."""
    batch_id: int
    batch_code: str
    test_date: datetime
    ph: float
    humidity: float
    nitrogen_percent: float
    phosphorus_percent: float
    heavy_metals_compliant: bool
    pathogens_compliant: bool
    biosolid_class: str  # 'A' or 'B'
    certified_by: str
    lab_reference: Optional[str]
    meets_regulatory_standards: bool
    notes: Optional[str]


# ==================== QUERY DTOs ====================

class BatchFilterDTO(BaseModel):
    """DTO for filtering batches."""
    treatment_plant_id: Optional[int] = None
    status: Optional[str] = None
    biosolid_class: Optional[str] = None
    has_available_stock: Optional[bool] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class TreatmentPlantFilterDTO(BaseModel):
    """DTO for filtering treatment plants."""
    region: Optional[str] = None
    is_active: Optional[bool] = None
    has_available_batches: Optional[bool] = None


# ==================== VALIDATION DTOs ====================

class StockAvailabilityCheckRequestDTO(BaseModel):
    """Request to check if batch has available stock."""
    batch_id: int = Field(gt=0)
    required_weight_kg: float = Field(gt=0)


class StockAvailabilityCheckResponseDTO(BaseModel):
    """Response from stock availability check."""
    is_available: bool
    batch_code: str
    available_volume_m3: float
    required_volume_m3: float
    can_fulfill: bool
    shortfall_m3: float = 0.0
    alternative_batches: list[int] = []
    warnings: list[str] = []


# ==================== DASHBOARD DTOs ====================

class TreatmentDashboardDTO(BaseModel):
    """Aggregated metrics for treatment operations dashboard."""
    active_batches: int
    batches_ready_for_dispatch: int
    total_available_volume_m3: float
    total_reserved_volume_m3: float
    average_treatment_days: float
    batches_by_class: dict[str, int]  # {'A': 5, 'B': 3}
    batches_by_status: dict[str, int]  # {'Ready': 4, 'Processing': 2}
    quality_issues_count: int
    plants_operating: int
    total_plants: int


# ==================== EXAMPLE USAGE ====================

"""
Example: Batch Management with Pydantic
----------------------------------------

```python
import streamlit as st
from domain.processing.dtos import (
    BatchCreateRequestDTO, 
    BatchResponseDTO,
    StockReservationRequestDTO
)

def create_batch_form():
    st.subheader("Create Treatment Batch")
    
    plant = st.selectbox("Treatment Plant", plants)
    source = st.selectbox("Source Type", ["Municipal", "Industrial"])
    volume = st.number_input("Initial Volume (m³)", min_value=0.1)
    solids = st.number_input("Solids %", min_value=0.0, max_value=100.0)
    
    if st.button("Create Batch"):
        try:
            request = BatchCreateRequestDTO(
                treatment_plant_id=plant.id,
                source_type=source,
                initial_volume_m3=volume,
                initial_solids_percent=solids,
                treatment_start_date=datetime.now()
            )
            
            response: BatchResponseDTO = (
                container.processing_app_service.create_batch(request)
            )
            
            st.success(f"Batch {response.code} created")
            st.info(f"Available volume: {response.available_volume_m3:.1f} m³")
            
        except ValidationError as e:
            st.error(f"Validation error: {e}")


def reserve_stock_form():
    batch = st.selectbox("Batch", available_batches)
    weight = st.number_input("Weight to Reserve (kg)", min_value=0.0)
    
    if st.button("Reserve"):
        try:
            request = StockReservationRequestDTO(
                batch_id=batch.id,
                weight_kg=weight,
                reserved_by=st.session_state.user_name
            )
            
            # Will validate that weight > 0 automatically
            response = container.processing_app_service.reserve_stock(request)
            
            st.success("Stock reserved")
            
        except ValidationError as e:
            st.error(f"Invalid weight: {e}")
```

Example: Quality Control with Validation
-----------------------------------------

```python
from domain.processing.dtos import TreatmentReceptionRequestDTO

def reception_form():
    load = st.selectbox("Load", pending_loads)
    
    reception_time = st.datetime_input("Reception Time")
    discharge_time = st.datetime_input("Discharge Time")
    
    ph = st.number_input("pH", min_value=4.0, max_value=10.0)
    humidity = st.number_input("Humidity %", min_value=0.0, max_value=100.0)
    
    if st.button("Register Reception"):
        try:
            request = TreatmentReceptionRequestDTO(
                load_id=load.id,
                reception_time=reception_time,
                discharge_time=discharge_time,  # Pydantic ensures > reception_time
                quality_ph=ph,
                quality_humidity=humidity
            )
            
            response = container.processing_app_service.register_reception(request)
            st.success("Reception registered")
            
        except ValidationError as e:
            st.error(f"Invalid times or values: {e}")
```
"""

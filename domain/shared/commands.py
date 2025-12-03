"""
Command Objects (DTOs) for UI Operations

These command objects represent user actions from the UI layer.
They use Pydantic for validation and type safety.

Benefits:
- Type safety (IDE autocomplete)
- Automatic validation before service calls
- Self-documenting (clear input requirements)
- Prevents "20 parameter" methods
- Easy to test and mock

Pattern:
    UI Form → Command Object → Application Service → Domain Service

Example:
    # In UI
    command = CreateLoadCommand(
        origin_id=facility.id,
        driver_id=driver.id,
        weight_net=weight  # Validated: must be > 0
    )
    
    # In Application Service
    def create_load(self, command: CreateLoadCommand) -> LoadCreatedEvent:
        # Data is already validated by Pydantic
        load = self.logistics_service.create_load(
            **command.dict()
        )
        return LoadCreatedEvent(load_id=load.id)
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ============================================================================
# LOGISTICS COMMANDS
# ============================================================================

class CreateLoadCommand(BaseModel):
    """
    Command to create a new load/transport request.
    
    Validation:
    - All IDs must be positive
    - weight_net must be > 0 and <= 50000 kg (50 tons max)
    """
    origin_facility_id: int = Field(gt=0, description="Origin facility ID")
    driver_id: int = Field(gt=0, description="Assigned driver ID")
    vehicle_id: int = Field(gt=0, description="Assigned vehicle ID")
    destination_site_id: Optional[int] = Field(None, gt=0, description="Destination site ID (for disposal)")
    treatment_plant_id: Optional[int] = Field(None, gt=0, description="Treatment plant ID (for treatment)")
    batch_id: Optional[int] = Field(None, gt=0, description="Source batch ID")
    
    weight_net: float = Field(
        gt=0, 
        le=50000, 
        description="Net weight in kg (max 50 tons)"
    )
    
    guide_number: Optional[str] = Field(None, max_length=50)
    container_id: Optional[int] = Field(None, gt=0)
    requested_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    
    @model_validator(mode='after')
    def validate_destination(self):
        """Ensure either site or plant is specified."""
        if not self.destination_site_id and not self.treatment_plant_id:
            raise ValueError("Must specify either destination_site_id or treatment_plant_id")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin_facility_id": 1,
                "driver_id": 5,
                "vehicle_id": 3,
                "destination_site_id": 10,
                "weight_net": 15000.0,
                "guide_number": "GTR-2024-001"
            }
        }


class RegisterArrivalCommand(BaseModel):
    """
    Command to register load arrival at destination (Gate In).
    
    Validation:
    - arrival_time cannot be in future
    - weight_gross must be positive if provided
    - pH must be between 4.0 and 10.0
    - humidity must be 0-100%
    """
    load_id: int = Field(gt=0)
    arrival_time: datetime
    weight_gross: Optional[float] = Field(None, gt=0, le=50000)
    ph: Optional[float] = Field(None, ge=4.0, le=10.0, description="pH value")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity %")
    observation: Optional[str] = Field(None, max_length=500)
    
    @field_validator('arrival_time')
    @classmethod
    def validate_arrival_not_future(cls, v):
        if v > datetime.now():
            raise ValueError("Arrival time cannot be in the future")
        return v


class CloseIncorporationCommand(BaseModel):
    """
    Command to close biosolid incorporation (DO-13 from Excel).
    
    This is a complex operation with many fields from the Excel checklist.
    
    Validation:
    - GPS coordinates format
    - Times in sequence (start < end)
    - Dosis within acceptable range
    """
    load_id: int = Field(gt=0)
    
    # GPS Coordinates
    gps_latitude: float = Field(ge=-90, le=90)
    gps_longitude: float = Field(ge=-180, le=180)
    gps_timestamp: datetime
    
    # Incorporation Details
    incorporation_start_time: datetime
    incorporation_end_time: datetime
    
    # Equipment and Personnel
    machine_id: Optional[int] = Field(None, gt=0)
    operator_name: str = Field(min_length=1, max_length=100)
    
    # Application Details
    application_method: str = Field(
        min_length=1, 
        max_length=50,
        description="Method: 'Superficie', 'Incorporado', 'Inyección'"
    )
    dosis_applied_tons_ha: Optional[float] = Field(
        None, 
        ge=0, 
        le=100,
        description="Applied dose in tons/hectare"
    )
    area_covered_ha: Optional[float] = Field(None, gt=0)
    
    # Quality/Compliance
    incorporation_depth_cm: Optional[float] = Field(None, ge=0, le=100)
    weather_condition: Optional[str] = Field(None, max_length=100)
    soil_moisture: Optional[str] = Field(None, max_length=50)
    
    # Final Notes
    final_observation: Optional[str] = Field(None, max_length=1000)
    
    @model_validator(mode='after')
    def validate_times(self):
        """Ensure incorporation end > start."""
        if self.incorporation_end_time <= self.incorporation_start_time:
            raise ValueError("Incorporation end time must be after start time")
        return self
    
    @field_validator('application_method')
    @classmethod
    def validate_method(cls, v):
        """Validate application method."""
        valid_methods = ['Superficie', 'Incorporado', 'Inyección', 'Subsuperficial']
        if v not in valid_methods:
            raise ValueError(f"Method must be one of: {', '.join(valid_methods)}")
        return v


class DispatchTruckCommand(BaseModel):
    """
    Command to dispatch a truck (legacy Sprint 2 flow).
    
    Combines batch selection, vehicle assignment, and dispatch in one operation.
    """
    batch_id: int = Field(gt=0)
    driver_id: int = Field(gt=0)
    vehicle_id: int = Field(gt=0)
    destination_site_id: int = Field(gt=0)
    origin_facility_id: int = Field(gt=0)
    weight_net: float = Field(gt=0, le=50000)
    guide_number: Optional[str] = Field(None, max_length=50)
    container_id: Optional[int] = Field(None, gt=0)


# ============================================================================
# AGRONOMY COMMANDS
# ============================================================================

class RegisterMachineryWorkCommand(BaseModel):
    """
    Command to register heavy machinery work.
    
    Validation:
    - horometer_end > horometer_start (fraud prevention)
    - end_time > start_time
    - fuel consumption realistic
    """
    machine_id: int = Field(gt=0)
    site_id: int = Field(gt=0)
    operator_name: str = Field(min_length=1, max_length=100)
    
    start_time: datetime
    end_time: datetime
    
    horometer_start: float = Field(ge=0, description="Starting horometer reading")
    horometer_end: float = Field(ge=0, description="Ending horometer reading")
    
    work_type: str = Field(
        min_length=1,
        max_length=100,
        description="'Incorporación', 'Nivelación', 'Arado'"
    )
    
    area_worked_ha: Optional[float] = Field(None, gt=0, le=1000)
    fuel_consumed_liters: Optional[float] = Field(None, ge=0, le=5000)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('horometer_end')
    @classmethod
    def validate_horometer(cls, v, info):
        """Prevent fraud: end must be > start."""
        if 'horometer_start' in info.data and v <= info.data['horometer_start']:
            raise ValueError("End horometer must be greater than start horometer (anti-fraud)")
        return v
    
    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, info):
        """End time must be after start time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError("End time must be after start time")
        return v
    
    @model_validator(mode='after')
    def validate_fuel_realistic(self):
        """Check if fuel consumption is realistic."""
        if self.fuel_consumed_liters and self.horometer_end and self.horometer_start:
            hours_worked = self.horometer_end - self.horometer_start
            if hours_worked > 0:
                liters_per_hour = self.fuel_consumed_liters / hours_worked
                if liters_per_hour > 50:  # Unrealistic consumption
                    raise ValueError(
                        f"Fuel consumption too high: {liters_per_hour:.1f} L/h "
                        "(max realistic: 50 L/h)"
                    )
        return self


class CreateSiteCommand(BaseModel):
    """Command to create a new disposal site."""
    name: str = Field(min_length=1, max_length=200)
    region: str = Field(min_length=1, max_length=100)
    commune: str = Field(min_length=1, max_length=100)
    total_area_ha: float = Field(gt=0, le=10000)
    agricultural_area_ha: Optional[float] = Field(None, ge=0)
    client_id: Optional[int] = Field(None, gt=0)
    is_active: bool = True
    
    @field_validator('agricultural_area_ha')
    @classmethod
    def validate_agricultural_area(cls, v, info):
        """Agricultural area cannot exceed total area."""
        if v is not None and 'total_area_ha' in info.data:
            if v > info.data['total_area_ha']:
                raise ValueError("Agricultural area cannot exceed total area")
        return v


class RegisterSiteEventCommand(BaseModel):
    """
    Command to register a site event (preparation, closure, inspection).
    """
    site_id: int = Field(gt=0)
    event_type: str = Field(min_length=1, max_length=50)
    event_date: datetime
    description: Optional[str] = Field(None, max_length=500)
    performed_by: Optional[str] = Field(None, max_length=100)
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Validate event type."""
        valid_types = [
            'Preparación', 'Cierre', 'Inspección', 
            'Muestreo', 'Mantención', 'Otro'
        ]
        if v not in valid_types:
            raise ValueError(f"Event type must be one of: {', '.join(valid_types)}")
        return v


# ============================================================================
# PROCESSING COMMANDS
# ============================================================================

class CreateBatchCommand(BaseModel):
    """Command to create a new treatment batch."""
    treatment_plant_id: int = Field(gt=0)
    source_type: str = Field(min_length=1, max_length=50)
    initial_volume_m3: float = Field(gt=0, le=10000)
    initial_solids_percent: Optional[float] = Field(None, ge=0, le=100)
    treatment_start_date: datetime
    operator_name: Optional[str] = Field(None, max_length=100)


class ReserveStockCommand(BaseModel):
    """Command to reserve stock from a batch for dispatch."""
    batch_id: int = Field(gt=0)
    weight_kg: float = Field(gt=0, le=50000)
    reserved_by: str = Field(min_length=1, max_length=100)
    reservation_date: Optional[datetime] = None


class RegisterTreatmentReceptionCommand(BaseModel):
    """
    Command to register reception of biosolids at treatment plant.
    """
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
        """Discharge must be after reception."""
        if 'reception_time' in info.data and v < info.data['reception_time']:
            raise ValueError("Discharge time must be after reception time")
        return v


# ============================================================================
# MASTER DATA COMMANDS
# ============================================================================

class CreateVehicleCommand(BaseModel):
    """Command to create a new vehicle."""
    plate: str = Field(min_length=1, max_length=20)
    type: str = Field(min_length=1, max_length=50)
    capacity_kg: Optional[float] = Field(None, gt=0, le=100000)
    is_active: bool = True


class CreateDriverCommand(BaseModel):
    """Command to create a new driver."""
    name: str = Field(min_length=1, max_length=100)
    license_number: str = Field(min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
Example: Using Commands in UI
------------------------------

```python
import streamlit as st
from pydantic import ValidationError
from domain.logistics.commands import CloseIncorporationCommand

def close_incorporation_form():
    st.subheader("DO-13: Cierre de Incorporación")
    
    # Collect form data
    load_id = st.number_input("Load ID", min_value=1)
    
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0)
        start = st.datetime_input("Start Time")
    with col2:
        lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0)
        end = st.datetime_input("End Time")
    
    operator = st.text_input("Operator Name")
    method = st.selectbox("Method", ["Superficie", "Incorporado", "Inyección"])
    
    if st.button("Complete Incorporation"):
        try:
            # Create command (automatic validation)
            command = CloseIncorporationCommand(
                load_id=load_id,
                gps_latitude=lat,
                gps_longitude=lon,
                gps_timestamp=datetime.now(),
                incorporation_start_time=start,
                incorporation_end_time=end,
                operator_name=operator,
                application_method=method
            )
            
            # Command is validated! Safe to call service
            result = container.agronomy_app_service.close_incorporation(command)
            
            st.success(f"Incorporation closed successfully! ID: {result.id}")
            
        except ValidationError as e:
            # Show validation errors to user
            st.error("Validation errors:")
            for error in e.errors():
                field = error['loc'][0]
                message = error['msg']
                st.error(f"❌ {field}: {message}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
```

Example: Using Commands in Application Service
-----------------------------------------------

```python
from domain.logistics.commands import CreateLoadCommand, LoadCreatedEvent

class LogisticsApplicationService:
    def create_load(self, command: CreateLoadCommand) -> LoadCreatedEvent:
        # No need to validate - Pydantic already did!
        # No need to check weight > 0, IDs positive, etc.
        
        # Just use the clean data
        load = self.logistics_service.create_load(
            origin_facility_id=command.origin_facility_id,
            driver_id=command.driver_id,
            vehicle_id=command.vehicle_id,
            destination_site_id=command.destination_site_id,
            weight_net=command.weight_net,
            guide_number=command.guide_number
        )
        
        return LoadCreatedEvent(
            load_id=load.id,
            manifest_code=load.manifest_code
        )
```

Benefits of This Pattern
-------------------------

1. **Type Safety**: IDE knows all fields and types
2. **Validation**: Automatic before service call
3. **Documentation**: Command class documents required fields
4. **Testability**: Easy to create mock commands
5. **Maintainability**: Add fields without changing method signatures
6. **Error Messages**: Clear validation errors for users

No More This:
```python
def create_load(origin, driver, truck, dest, weight, guide, container, date, ...):
    # 20 parameters!
    if weight <= 0:
        raise ValueError("Weight must be positive")
    if not origin:
        raise ValueError("Origin required")
    # ... endless validation
```

Instead This:
```python
def create_load(command: CreateLoadCommand):
    # Already validated!
    # Just use command.weight_net, command.origin_id, etc.
```
"""

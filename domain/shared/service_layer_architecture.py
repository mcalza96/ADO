"""
Service Layer Architecture Documentation.

This module defines the three-tier service architecture used in the application:

1. **Repository Layer** - Data access only, returns Entities
2. **Domain Service Layer** - Business logic, no UI knowledge
3. **Application Service Layer** - Use cases, orchestrates domain services

┌─────────────────────────────────────────────────────────────┐
│                        UI Layer (Streamlit)                  │
│                   (Presentation Logic Only)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Application Services (Use Cases)                │
│   - Orchestrate domain services                             │
│   - Handle DTOs from UI                                      │
│   - Coordinate transactions                                  │
│   - Return DTOs to UI                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Domain Services                            │
│   - Business rules and calculations                          │
│   - Domain logic (validators, calculators)                   │
│   - No knowledge of UI or database                           │
│   - Work with Entities                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Repositories                            │
│   - SQL queries only                                         │
│   - CRUD operations                                          │
│   - Returns Entities (domain objects)                        │
│   - No business logic                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database (PostgreSQL)                      │
└─────────────────────────────────────────────────────────────┘


EXAMPLES
--------

❌ INCORRECT - Repository with business logic:
```python
class LoadRepository:
    def get_dispatchable_loads(self):
        # BAD: Business rule in repository
        return self.execute_query(
            "SELECT * FROM loads WHERE status = 'Pending' AND batch_id IS NOT NULL"
        )
```

✅ CORRECT - Repository only does SQL:
```python
class LoadRepository:
    def get_by_status(self, status: str) -> List[Load]:
        # GOOD: Pure data access
        return self.execute_query("SELECT * FROM loads WHERE status = ?", (status,))
```

❌ INCORRECT - Domain service talks to UI:
```python
class LogisticsDomainService:
    def dispatch_truck(self, ...):
        result = self._create_load()
        # BAD: Domain service knows about Streamlit
        st.success(f"Load {result.id} created!")
        return result
```

✅ CORRECT - Domain service returns data:
```python
class LogisticsDomainService:
    def dispatch_truck(self, ...) -> Load:
        # GOOD: Just returns the entity
        load = Load(...)
        return self.load_repo.create(load)
```

❌ INCORRECT - UI has business logic:
```python
def dispatch_form():
    # BAD: Calculation in UI layer
    nitrogen_kg = weight * 0.05 * batch.nitrogen_percent / 100
    if nitrogen_kg > site.remaining_capacity:
        st.error("Exceeds capacity!")
```

✅ CORRECT - UI calls application service:
```python
def dispatch_form():
    # GOOD: UI only handles presentation
    try:
        container.logistics.dispatch_service.dispatch_truck(...)
        st.success("Dispatched successfully!")
    except ComplianceViolationError as e:
        st.error(str(e))
```


NAMING CONVENTIONS
------------------

Repository methods:
    - get_by_id(id: int) -> Entity
    - get_all() -> List[Entity]
    - get_by_attribute(attr: str, value: Any) -> List[Entity]
    - create(entity: Entity) -> Entity
    - update(entity: Entity) -> Entity
    - delete(id: int) -> bool

Domain Service methods:
    - calculate_*(...) -> float/int
    - validate_*(...) -> bool
    - can_*(...) -> bool
    - register_*(...) -> Entity
    - apply_*(...) -> Entity

Application Service methods (Use Cases):
    - create_*(...) -> DTO
    - dispatch_*(...) -> DTO
    - complete_*(...) -> DTO
    - get_*_for_view(...) -> DTO


MIGRATION CHECKLIST
-------------------

When refactoring an existing service:

1. ✓ Move SQL to Repository
   - Remove execute_query() from services
   - Create specific repository methods

2. ✓ Extract business logic to Domain Services
   - Calculators (nitrogen, weight, cost)
   - Validators (capacity, compliance)
   - Rules engines (state machines)

3. ✓ Create Application Services for Use Cases
   - Each UI flow gets an application service method
   - Method receives DTOs, returns DTOs
   - Coordinates domain services and repositories

4. ✓ Update UI to use Application Services
   - Remove business logic from views
   - Call application services
   - Handle DTOs only


CURRENT STATE vs TARGET STATE
------------------------------

Current (Mixed):
    UI -> LogisticsDomainService (SQL + Logic + Coordination)

Target (Clean):
    UI -> DispatchApplicationService -> LogisticsDomainService -> LoadRepository
                                     -> ComplianceDomainService
                                     -> ManifestDomainService

"""

from typing import TypeVar, Generic, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# Type variable for generic repository
T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Interface for all repositories.
    
    Repositories are responsible ONLY for data access.
    NO business logic allowed.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve entity by ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all entities."""
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity."""
        pass


class IDomainService(ABC):
    """
    Interface for domain services.
    
    Domain services contain business logic and rules.
    They work with entities, not DTOs.
    They have NO knowledge of UI or database implementation.
    """
    
    # Domain services define their own methods based on business needs
    # Examples:
    # - calculate_nitrogen_load(batch_id: int, weight: float) -> float
    # - validate_dispatch(batch_id: int, site_id: int) -> bool
    # - can_close_load(load_id: int) -> bool
    pass


class IApplicationService(ABC):
    """
    Interface for application services (use cases).
    
    Application services orchestrate domain services and repositories.
    They receive DTOs from UI and return DTOs to UI.
    They handle transaction boundaries.
    """
    
    # Application services define use case methods
    # Examples:
    # - execute_dispatch(request: DispatchRequestDTO) -> DispatchResponseDTO
    # - complete_reception(request: ReceptionRequestDTO) -> ReceptionResponseDTO
    pass


@dataclass
class BaseDTO:
    """
    Base class for Data Transfer Objects.
    
    DTOs are used to transfer data between UI and Application Services.
    They are NOT domain entities - they are flattened views optimized
    for UI consumption.
    """
    pass


# Example DTOs to illustrate the pattern

@dataclass
class DispatchRequestDTO(BaseDTO):
    """
    DTO for dispatch truck use case.
    Received from UI layer.
    """
    batch_id: int
    driver_id: int
    vehicle_id: int
    destination_site_id: int
    origin_facility_id: int
    weight_net: float
    guide_number: Optional[str] = None
    container_id: Optional[int] = None


@dataclass
class DispatchResponseDTO(BaseDTO):
    """
    DTO returned to UI layer after dispatch.
    Contains all info needed to display result.
    """
    success: bool
    load_id: Optional[int] = None
    manifest_code: Optional[str] = None
    manifest_path: Optional[str] = None
    nitrogen_applied_kg: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class SiteCapacityDTO(BaseDTO):
    """
    DTO for displaying site capacity information.
    Flattened for easy display in UI.
    """
    site_id: int
    site_name: str
    total_area_ha: float
    nitrogen_limit_kg: float
    nitrogen_applied_kg: float
    nitrogen_remaining_kg: float
    capacity_percent_used: float
    can_accept_more: bool
    status: str  # 'Available', 'Near Limit', 'At Capacity'


# Example showing the flow

"""
Example: Dispatch Truck Flow
-----------------------------

1. UI Layer (Streamlit):
```python
def dispatch_form():
    batch = st.selectbox("Batch", batches)
    driver = st.selectbox("Driver", drivers)
    vehicle = st.selectbox("Vehicle", vehicles)
    site = st.selectbox("Site", sites)
    weight = st.number_input("Weight (kg)")
    
    if st.button("Dispatch"):
        # Create DTO from form
        request = DispatchRequestDTO(
            batch_id=batch.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            destination_site_id=site.id,
            origin_facility_id=current_facility_id,
            weight_net=weight
        )
        
        # Call application service
        response = container.dispatch_application_service.execute_dispatch(request)
        
        # Display result
        if response.success:
            st.success(f"Load {response.manifest_code} dispatched!")
            st.download_button("Manifest", response.manifest_path)
        else:
            st.error(response.error_message)
```

2. Application Service Layer:
```python
class DispatchApplicationService(IApplicationService):
    def execute_dispatch(self, request: DispatchRequestDTO) -> DispatchResponseDTO:
        try:
            # 1. Validate using domain service
            self.compliance_service.validate_dispatch(
                request.batch_id, 
                request.destination_site_id, 
                request.weight_net
            )
            
            # 2. Execute dispatch using domain service
            load = self.logistics_service.dispatch_truck(
                batch_id=request.batch_id,
                driver_id=request.driver_id,
                vehicle_id=request.vehicle_id,
                destination_site_id=request.destination_site_id,
                origin_facility_id=request.origin_facility_id,
                weight_net=request.weight_net
            )
            
            # 3. Generate manifest
            manifest = self.manifest_service.generate_manifest(load.id)
            
            # 4. Calculate nitrogen
            agronomics = self.compliance_service.calculate_load_agronomics(
                request.batch_id, request.weight_net
            )
            
            # 5. Return DTO
            return DispatchResponseDTO(
                success=True,
                load_id=load.id,
                manifest_code=load.manifest_code,
                manifest_path=manifest.file_path,
                nitrogen_applied_kg=agronomics['total_n_kg']
            )
            
        except ComplianceViolationError as e:
            return DispatchResponseDTO(
                success=False,
                error_message=str(e)
            )
```

3. Domain Service Layer:
```python
class LogisticsDomainService(IDomainService):
    def dispatch_truck(self, batch_id, driver_id, vehicle_id, ...) -> Load:
        # Pure business logic
        load = Load(
            batch_id=batch_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            destination_site_id=destination_site_id,
            ...
        )
        
        # Create load
        created_load = self.load_repo.create(load)
        
        # Reserve stock
        self.batch_service.reserve_stock(batch_id, weight_net)
        
        return created_load
```

4. Repository Layer:
```python
class LoadRepository(IRepository[Load]):
    def create(self, load: Load) -> Load:
        # Pure SQL, no business logic
        query = '''
            INSERT INTO loads (batch_id, driver_id, vehicle_id, ...)
            VALUES (?, ?, ?, ...)
            RETURNING *
        '''
        result = self.execute_query(query, (...))
        return Load.from_db_row(result[0])
```
"""

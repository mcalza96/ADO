# Architecture Diagrams

## 1. Bounded Contexts (Container Organization)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Dependency Container                         │
│                    (config/dependencies.py)                      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ├─── LogisticsContainer
                               │    ├── dispatch_service
                               │    ├── vehicle_service
                               │    ├── driver_service
                               │    ├── contractor_service
                               │    └── container_service
                               │
                               ├─── AgronomyContainer
                               │    ├── location_service
                               │    ├── agronomy_service
                               │    ├── disposal_service
                               │    ├── machinery_service
                               │    └── field_reception_handler
                               │
                               ├─── ProcessingContainer
                               │    ├── batch_service
                               │    ├── reception_service
                               │    ├── treatment_service
                               │    ├── facility_service
                               │    └── treatment_plant_service
                               │
                               ├─── ComplianceContainer
                               │    ├── compliance_service
                               │    └── compliance_listener
                               │
                               ├─── ReportingContainer
                               │    ├── reporting_service
                               │    ├── dashboard_service
                               │    └── manifest_service
                               │
                               ├─── MastersContainer
                               │    ├── client_service
                               │    └── auth_service
                               │
                               ├─── SatelliteContainer
                               │    ├── maintenance_listener
                               │    └── costing_listener
                               │
                               └─── UIContainer
                                    └── task_resolver
```

## 2. Service Layer Architecture (3-Tier)

```
┌───────────────────────────────────────────────────────────────────────┐
│                          UI Layer (Streamlit)                          │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Dispatch     │  │ Reception    │  │ Site         │               │
│  │ View         │  │ View         │  │ Management   │  ...          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                         │
│         │    Calls with   │                 │                         │
│         └────────DTOs─────┴─────────────────┘                         │
└───────────────────────────────────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│               Application Services (Use Cases / Orchestration)         │
│                                                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐                    │
│  │ DispatchApp         │  │ ReceptionApp        │                    │
│  │ Service             │  │ Service             │  ...               │
│  │                     │  │                     │                    │
│  │ - execute_dispatch  │  │ - register_arrival  │                    │
│  │ - check_compliance  │  │ - close_trip        │                    │
│  └──────────┬──────────┘  └──────────┬──────────┘                    │
│             │                        │                                │
│             │   Orchestrates         │                                │
│             └────────────┬───────────┘                                │
└───────────────────────────────────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    Domain Services (Business Logic)                    │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Logistics    │  │ Compliance   │  │ Agronomy     │               │
│  │ Domain       │  │ Service      │  │ Domain       │  ...          │
│  │ Service      │  │              │  │ Service      │               │
│  │              │  │ - validate   │  │              │               │
│  │ - dispatch   │  │ - calculate  │  │ - register   │               │
│  │ - transit    │  │ - check      │  │ - track      │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                         │
│         │    Uses         │                 │                         │
│         └─────────────────┴─────────────────┘                         │
└───────────────────────────────────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    Repositories (Data Access Only)                     │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Load         │  │ Batch        │  │ Site         │               │
│  │ Repository   │  │ Repository   │  │ Repository   │  ...          │
│  │              │  │              │  │              │               │
│  │ - get_by_id  │  │ - get_by_id  │  │ - get_by_id  │               │
│  │ - create     │  │ - create     │  │ - create     │               │
│  │ - update     │  │ - update     │  │ - update     │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                         │
│         │     SQL         │                 │                         │
│         └─────────────────┴─────────────────┘                         │
└───────────────────────────────────────────────────────────────────────┘
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        Database (PostgreSQL)                           │
│                                                                        │
│  [loads]  [batches]  [sites]  [vehicles]  [drivers]  ...             │
└───────────────────────────────────────────────────────────────────────┘
```

## 3. Dispatch Flow Example

```
User Fills Form                    Pydantic Validates                App Service Orchestrates              Domain Services Execute            Repository Persists
     │                                    │                                  │                                      │                              │
     │  dispatch_truck_view()             │                                  │                                      │                              │
     │                                    │                                  │                                      │                              │
     ▼                                    ▼                                  │                                      │                              │
┌─────────┐                        ┌──────────┐                             │                                      │                              │
│ Batch   │                        │ Dispatch │                             │                                      │                              │
│ Weight  │────────────────────>   │ Request  │                             │                                      │                              │
│ Driver  │    Create DTO          │ DTO      │                             │                                      │                              │
│ Site    │                        │          │                             │                                      │                              │
└─────────┘                        │ Validated│─────────────────>           │                                      │                              │
                                   │ ✓ weight>0│     execute_dispatch()     │                                      │                              │
                                   │ ✓ IDs>0  │                             ▼                                      │                              │
                                   │ ✓ w<=50k │                      ┌──────────────┐                             │                              │
                                   └──────────┘                      │ Dispatch     │                             │                              │
                                                                     │ App Service  │                             │                              │
                                                                     └──────┬───────┘                             │                              │
                                                                            │                                      │                              │
                                                                            │ 1. validate_dispatch()               │                              │
                                                                            ├──────────────────────────────────────>│                              │
                                                                            │                                      │ ComplianceService            │
                                                                            │                                      │ .validate_dispatch()         │
                                                                            │                                      │                              │
                                                                            │ 2. dispatch_truck()                  │                              │
                                                                            ├──────────────────────────────────────>│                              │
                                                                            │                                      │ LogisticsDomainService       │
                                                                            │                                      │ .dispatch_truck()            │
                                                                            │                                      │    ├────────────────────────>│
                                                                            │                                      │    │ load_repo.create()      │ LoadRepository
                                                                            │                                      │    │                         │ .create()
                                                                            │                                      │    │                         │    │
                                                                            │                                      │    │                         │    │ INSERT INTO loads
                                                                            │                                      │    │<────────────────────────│    │
                                                                            │                                      │    │ Load entity             │    ▼
                                                                            │                                      │    │                         │ Database
                                                                            │ 3. register_nitrogen()               │    │                         │
                                                                            ├──────────────────────────────────────>│────┤                         │
                                                                            │                                      │    │                         │
                                                                            │                                      │ AgronomyDomainService        │
                                                                            │                                      │ .register_nitrogen()         │
                                                                            │                                      │                              │
                                                                            │ 4. generate_manifest()               │                              │
                                                                            ├──────────────────────────────────────>│                              │
                                                                            │                                      │                              │
                                                                            │                                      │ ManifestService              │
                                                                            │                                      │ .generate_manifest()         │
                                                                            │                                      │                              │
                                                                            │<─────────────────────────────────────┤                              │
                                                                            │ All operations complete              │                              │
                                                                            │                                      │                              │
                                                                            ▼                                      │                              │
                                                                     ┌──────────────┐                             │                              │
                                                                     │ Dispatch     │                             │                              │
                                                                     │ Response DTO │                             │                              │
                                                                     │              │                             │                              │
                                                                     │ success=True │                             │                              │
                                                                     │ load_id=123  │                             │                              │
                                                                     │ manifest=... │                             │                              │
                                                                     └──────┬───────┘                             │                              │
                                                                            │                                      │                              │
                                                                            │ Return to UI                         │                              │
     ▲                                                                      │                                      │                              │
     │                                                                      │                                      │                              │
┌─────────┐                                                                │                                      │                              │
│ Success │<───────────────────────────────────────────────────────────────┘                                      │                              │
│ Message │                                                                                                       │                              │
│ + Data  │                                                                                                       │                              │
└─────────┘                                                                                                       │                              │
```

## 4. Data Flow with DTOs

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              BEFORE (Dictionary Hell)                             │
└──────────────────────────────────────────────────────────────────────────────────┘

UI                              Service                             Database
│                                │                                    │
│  data = {                      │                                    │
│    "batch_id": 123,            │                                    │
│    "weight": -100,  ← ❌ Bug!  │                                    │
│    "driver": "John" ← ❌ Should be ID!                              │
│  }                             │                                    │
│                                │                                    │
├────────────────────────────────>│                                    │
│  dispatch_truck(**data)        │                                    │
│                                │  ❌ Runtime error in SQL!          │
│                                ├────────────────────────────────────>│
│                                │  INSERT ... weight=-100            │
│                                │  ❌ Constraint violation!          │


┌──────────────────────────────────────────────────────────────────────────────────┐
│                              AFTER (Pydantic DTOs)                                │
└──────────────────────────────────────────────────────────────────────────────────┘

UI                              DTO Validation                 App Service          Domain Service        Database
│                                │                                │                     │                   │
│  request = DispatchRequestDTO( │                                │                     │                   │
│    batch_id=123,               │                                │                     │                   │
│    weight_net=-100  ← ❌       │                                │                     │                   │
│  )                             │                                │                     │                   │
│                                │                                │                     │                   │
├────────────────────────────────>│                                │                     │                   │
│                                │  ✓ Validate weight > 0         │                     │                   │
│                                │  ❌ ValidationError!            │                     │                   │
│<───────────────────────────────┤                                │                     │                   │
│  "weight must be positive"     │                                │                     │                   │
│                                │                                │                     │                   │
│  ────── User fixes ──────>     │                                │                     │                   │
│                                │                                │                     │                   │
│  request = DispatchRequestDTO( │                                │                     │                   │
│    batch_id=123,               │                                │                     │                   │
│    weight_net=15000 ✓          │                                │                     │                   │
│  )                             │                                │                     │                   │
│                                │                                │                     │                   │
├────────────────────────────────>│                                │                     │                   │
│                                │  ✓ All validations pass        │                     │                   │
│                                ├────────────────────────────────>│                     │                   │
│                                │                                │  ✓ Type-safe        │                   │
│                                │                                ├─────────────────────>│                   │
│                                │                                │                     │  ✓ Valid entity   │
│                                │                                │                     ├───────────────────>│
│                                │                                │                     │  ✓ SUCCESS        │
```

## 5. Bounded Context Communication

```
┌────────────────┐         ┌────────────────┐         ┌────────────────┐
│   Logistics    │         │   Compliance   │         │   Agronomy     │
│                │         │                │         │                │
│ dispatch_truck │────1───>│ validate_      │         │                │
│                │         │ dispatch       │         │                │
│                │         │                │         │                │
│                │<────2───│ is_compliant   │         │                │
│                │         │                │         │                │
│                │         │                │         │                │
│                │────3──────────────────────────────>│ register_      │
│                │         │                │         │ nitrogen       │
│                │         │                │         │                │
└────────────────┘         └────────────────┘         └────────────────┘
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
┌────────────────┐         ┌────────────────┐         ┌────────────────┐
│ LoadRepository │         │ SiteRepository │         │ Application    │
│                │         │                │         │ Repository     │
└────────────────┘         └────────────────┘         └────────────────┘

Legend:
  1. Logistics asks Compliance to validate before dispatch
  2. Compliance returns validation result
  3. Logistics notifies Agronomy of nitrogen application

Each bounded context has its own:
  - Services (business logic)
  - Repositories (data access)
  - DTOs (data transfer)
  - Entities (domain objects)

Communication happens through:
  - Direct service calls (synchronous)
  - Event bus (asynchronous, for satellite modules)
```

## 6. Migration Strategy (No Breaking Changes)

```
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 1: SETUP (✅ DONE)                        │
└─────────────────────────────────────────────────────────────────┘

Old container.py                    New config/dependencies.py
     (228 lines)                         (Modular)
         │                                    │
         │                                    │
         ├────────────────────────────────────┤
         │   Backward Compatibility Aliases   │
         │                                    │
         │   container.dispatch_service ──>   │
         │   container.logistics.dispatch_service
         │                                    │
         │   Both work! No breaking changes   │
         └────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│           PHASE 2: GRADUAL MIGRATION (In Progress)               │
└─────────────────────────────────────────────────────────────────┘

Step 1: Update imports (low risk)
   ui/dispatch_view.py:
     from container import get_container ──> from config.dependencies import get_container
     container.dispatch_service ──> container.logistics.dispatch_service

Step 2: Create application services (one at a time)
   domain/logistics/application_service.py ──> New file
   Wire up in LogisticsContainer
   Update UI to use app service

Step 3: Integrate Pydantic DTOs (incremental)
   ui/dispatch_view.py:
     Old: dispatch_service.dispatch_truck(batch_id, weight, ...)
     New: DispatchRequestDTO(...) ──> app_service.execute_dispatch(request)

Step 4: Refactor services (extract SQL to repos)
   Old: service has SQL
   New: service calls repository


┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: CLEANUP (Future)                           │
└─────────────────────────────────────────────────────────────────┘

When all UI migrated:
  - Remove backward compatibility aliases
  - Delete old container.py
  - Full type safety everywhere
  - Clean architecture achieved
```

## Key Principles

1. **Separation of Concerns**
   - UI: Presentation only
   - Application Service: Orchestration
   - Domain Service: Business logic
   - Repository: Data access

2. **Type Safety**
   - Pydantic DTOs validate at UI boundary
   - Catch errors early, before business logic
   - IDE autocomplete for better DX

3. **Testability**
   - Each layer can be tested independently
   - Easy to mock dependencies
   - DTOs make test data explicit

4. **Maintainability**
   - Clear boundaries between layers
   - Easy to find code (bounded contexts)
   - Self-documenting (DTOs, types)

5. **Scalability**
   - Easy to add new features
   - Can parallelize work on different contexts
   - Event bus for loose coupling

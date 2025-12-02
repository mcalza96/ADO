from typing import Optional, Dict, Any, List
from datetime import datetime
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from repositories.load_repository import LoadRepository
from models.operations.load import Load
from models.masters.vehicle import Vehicle
from models.masters.container import Container
from services.operations.batch_service import BatchService
from services.operations.treatment_batch_service import TreatmentBatchService
from services.compliance.compliance_service import ComplianceService
from services.operations.agronomy_domain_service import AgronomyDomainService
from services.operations.manifest_service import ManifestService
from domain.exceptions import TransitionException, ComplianceViolationError
from domain.constants import SLUDGE_DENSITY

class LogisticsDomainService:
    """
    Handles the complete Transport Lifecycle:
    Planning -> Dispatch -> Transit -> Reception -> Closing
    
    Consolidates:
    - LogisticsService (Planning)
    - DispatchService (Gate Out)
    - ReceptionService (Gate In)
    """
    def __init__(
        self,
        db_manager: DatabaseManager,
        batch_service: BatchService,
        compliance_service: ComplianceService,
        agronomy_service: AgronomyDomainService,
        manifest_service: ManifestService
    ):
        self.db_manager = db_manager
        self.load_repo = LoadRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
        self.container_repo = BaseRepository(db_manager, Container, "containers")
        
        self.batch_service = batch_service
        self.treatment_batch_service = TreatmentBatchService(db_manager)
        self.compliance_service = compliance_service
        self.agronomy_service = agronomy_service
        self.manifest_service = manifest_service

    # --- Planning Phase ---
    def create_request(self, facility_id: Optional[int], requested_date: datetime, plant_id: Optional[int] = None) -> Load:
        load = Load(
            id=None,
            origin_facility_id=facility_id,
            origin_treatment_plant_id=plant_id,
            status='Requested',
            requested_date=requested_date,
            created_at=datetime.now()
        )
        return self.load_repo.add(load)

    def schedule_load(self, load_id: int, driver_id: int, vehicle_id: int, scheduled_date: datetime, 
                         site_id: Optional[int] = None, treatment_plant_id: Optional[int] = None, 
                         container_quantity: Optional[int] = None) -> bool:
        if not site_id and not treatment_plant_id:
            raise ValueError("Must provide either a Destination Site or a Treatment Plant.")
            
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError("Load not found")
            
        if load.status != 'Requested':
            raise TransitionException(f"Cannot schedule load. Current status: {load.status}. Expected: 'Requested'.")
        
        load.driver_id = driver_id
        load.vehicle_id = vehicle_id
        load.container_quantity = container_quantity
        
        if treatment_plant_id:
            load.destination_treatment_plant_id = treatment_plant_id
            load.destination_site_id = None
        else:
            load.destination_site_id = site_id
            load.destination_treatment_plant_id = None
            
        load.scheduled_date = scheduled_date
        load.status = 'Scheduled'
        load.updated_at = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        
        return self.load_repo.update(load)

    # --- Dispatch Phase (Gate Out) ---
    def _validate_capacity(self, vehicle_id: int, container_id: Optional[int]) -> None:
        if not container_id:
            return 
        
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        container = self.container_repo.get_by_id(container_id)
        
        if not vehicle or not container:
            return 
            
        estimated_weight = container.capacity_m3 * SLUDGE_DENSITY
        if estimated_weight > vehicle.capacity_wet_tons:
             raise ValueError(f"Capacity Risk: Container {container.code} ({container.capacity_m3}m3) estimated weight ({estimated_weight:.2f}t) exceeds Vehicle {vehicle.license_plate} capacity ({vehicle.capacity_wet_tons}t).")

    def dispatch_truck(
        self,
        batch_id: int,
        driver_id: int,
        vehicle_id: int,
        destination_site_id: int,
        origin_facility_id: int,
        weight_net: float,
        guide_number: Optional[str] = None,
        container_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dispatches a truck (Sprint 2 / Legacy Flow).
        """
        self._validate_capacity(vehicle_id, container_id)
        
        # Validation
        available = self.batch_service.get_batch_balance(batch_id)
        if weight_net > available:
            raise ValueError(f"Stock insuficiente. Disponible: {available} kg, Solicitado: {weight_net} kg")
            
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if weight_net > vehicle.max_capacity:
            raise ValueError(f"Peso excede capacidad del vehículo.")
            
        try:
            self.compliance_service.validate_dispatch(batch_id, destination_site_id, weight_net)
        except ComplianceViolationError as e:
            raise ValueError(f"🚫 OPERACIÓN BLOQUEADA: {str(e)}")

        with self.db_manager as conn:
            load = Load(
                id=None,
                origin_facility_id=origin_facility_id,
                destination_site_id=destination_site_id,
                batch_id=batch_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                container_id=container_id,
                weight_net=weight_net,
                guide_number=guide_number,
                status='InTransit',
                dispatch_time=datetime.now(),
                created_at=datetime.now()
            )
            
            created_load = self.load_repo.create_load(load)
            self.treatment_batch_service.reserve_stock(batch_id, weight_net)
            
            # Register Nitrogen
            self.agronomy_service.register_nitrogen_application(
                site_id=destination_site_id,
                load_id=created_load.id,
                batch_id=batch_id,
                weight_net=weight_net
            )
            
            manifest_path = self.manifest_service.generate_manifest(created_load.id)
            
            return {
                "status": "success",
                "load_id": created_load.id,
                "manifest_code": created_load.manifest_code,
                "manifest_path": manifest_path
            }

    def accept_trip(self, load_id: int) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != 'Scheduled':
            raise ValueError("Invalid load or status")
        load.status = 'Accepted'
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    def start_trip(self, load_id: int) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load or load.status != 'Accepted':
            raise ValueError("Invalid load or status")
        load.status = 'InTransit'
        load.dispatch_time = datetime.now()
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    # --- Reception Phase (Gate In) ---
    def register_arrival(self, load_id: int, weight_gross: float = None, ph: float = None, 
                        humidity: float = None, observation: str = None) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        load.register_arrival(weight_gross, ph, humidity, observation)
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    def close_trip(self, load_id: int, data_dict: Dict[str, Any]) -> bool:
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
            
        weight_net = data_dict.get('weight_net')
        ticket = data_dict.get('ticket_number')
        guide = data_dict.get('guide_number')
        ph = data_dict.get('quality_ph')
        humidity = data_dict.get('quality_humidity')
        
        if any(v is None for v in [weight_net, ticket, guide, ph, humidity]):
             raise ValueError("Missing required fields for closing trip")

        load.close_trip(
            weight_net=float(weight_net),
            ticket_number=ticket,
            guide_number=guide,
            ph=float(ph),
            humidity=float(humidity)
        )
        
        load.sync_status = 'PENDING'
        load.last_updated_local = datetime.now()
        return self.load_repo.update(load)

    # --- Queries ---
    def get_loads_by_facility(self, facility_id: int) -> List[Load]:
        return self.load_repo.get_all_filtered(origin_facility_id=facility_id)

    def get_loads_by_status(self, status: str) -> List[Load]:
        return self.load_repo.get_by_status(status)
        
    def get_planning_loads(self, status: str) -> List[dict]:
        return self.load_repo.get_loads_with_details(status=status)

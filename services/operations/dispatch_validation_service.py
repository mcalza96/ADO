from typing import Optional
from database.db_manager import DatabaseManager
from repositories.vehicle_repository import VehicleRepository
from services.operations.batch_service import BatchService
from services.compliance.compliance_service import ComplianceService
from domain.exceptions import ComplianceViolationError

class DispatchValidationService:
    """
    Handles all validation logic for dispatch operations.
    Extracted from DispatchService to comply with Single Responsibility Principle.
    """
    def __init__(
        self, 
        vehicle_repo: VehicleRepository,
        batch_service: BatchService,
        compliance_service: ComplianceService
    ):
        self.vehicle_repo = vehicle_repo
        self.batch_service = batch_service
        self.compliance_service = compliance_service

    def validate_dispatch(
        self,
        batch_id: int,
        vehicle_id: int,
        destination_site_id: int,
        weight_net: float
    ) -> None:
        """
        Validates a dispatch operation against all business rules.
        
        Args:
            batch_id: ID of the batch
            vehicle_id: ID of the vehicle
            destination_site_id: ID of the destination site
            weight_net: Net weight to dispatch (kg)
            
        Raises:
            ValueError: If any validation fails
        """
        # Validation 1: Check batch stock
        self._validate_batch_stock(batch_id, weight_net)
        
        # Validation 2: Check vehicle capacity
        self._validate_vehicle_capacity(vehicle_id, weight_net)
        
        # Validation 3: Compliance Check (Hard Constraints)
        self._validate_compliance(batch_id, destination_site_id, weight_net)

    def _validate_batch_stock(self, batch_id: int, weight_net: float) -> None:
        """Validates that sufficient batch stock is available."""
        available = self.batch_service.get_batch_balance(batch_id)
        if weight_net > available:
            raise ValueError(
                f"Stock insuficiente. Disponible: {available} kg, Solicitado: {weight_net} kg"
            )

    def _validate_vehicle_capacity(self, vehicle_id: int, weight_net: float) -> None:
        """Validates that the vehicle has sufficient capacity."""
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehículo con ID {vehicle_id} no encontrado")
        
        if weight_net > vehicle.max_capacity:
            raise ValueError(
                f"Peso excede capacidad del vehículo. Capacidad: {vehicle.max_capacity} kg, Peso: {weight_net} kg"
            )

    def _validate_compliance(self, batch_id: int, destination_site_id: int, weight_net: float) -> None:
        """Validates agronomic and regulatory compliance."""
        try:
            self.compliance_service.validate_dispatch(batch_id, destination_site_id, weight_net)
        except ComplianceViolationError as e:
            # Re-raise with a clear prefix for UI handling
            raise ValueError(f"🚫 OPERACIÓN BLOQUEADA: {str(e)}")

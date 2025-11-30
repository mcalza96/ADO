from typing import List, Optional
from datetime import datetime, date
from database.db_manager import DatabaseManager
from repositories.batch_repository import BatchRepository
from models.masters.treatment import Batch

class BatchService:
    """
    Service layer for Batch (Production Lot) management.
    Handles business logic for creating, querying, and managing biosolids production batches.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.batch_repo = BatchRepository(db_manager)

    def create_daily_batch(
        self, 
        facility_id: int, 
        batch_code: str, 
        production_date: date, 
        initial_tonnage: float,
        class_type: str,
        sludge_type: Optional[str] = None
    ) -> Batch:
        """
        Creates a new production batch with business validations.
        
        Args:
            facility_id: ID of the treatment facility
            batch_code: Unique batch identifier (e.g., 'L-2025-11-29-A')
            production_date: Date of production
            initial_tonnage: Initial tonnage in kg
            class_type: Biosolid classification ('A', 'B', 'NoClass')
            sludge_type: Optional type description
            
        Returns:
            Created Batch object
            
        Raises:
            ValueError: If validation fails
        """
        # Validation 1: Unique batch code
        existing = self.batch_repo.get_by_batch_code(batch_code)
        if existing:
            raise ValueError(f"El código de lote '{batch_code}' ya existe. Debe ser único.")
        
        # Validation 2: Positive tonnage
        if initial_tonnage <= 0:
            raise ValueError("El tonelaje inicial debe ser mayor a 0.")
        
        # Validation 3: Valid class type
        if class_type not in ['A', 'B', 'NoClass']:
            raise ValueError("La clase debe ser 'A', 'B' o 'NoClass'.")
        
        # Create batch
        batch = Batch(
            id=None,
            facility_id=facility_id,
            batch_code=batch_code,
            production_date=production_date,
            initial_tonnage=initial_tonnage,
            current_tonnage=initial_tonnage,  # Start with full stock
            class_type=class_type,
            sludge_type=sludge_type,
            status='Available',
            created_at=datetime.now()
        )
        
        return self.batch_repo.add(batch)

    def get_available_batches(self, facility_id: Optional[int] = None) -> List[Batch]:
        """
        Returns batches available for dispatch (status='Available', stock > 0).
        Optionally filtered by facility.
        """
        return self.batch_repo.get_available_batches(facility_id)

    def get_batch_balance(self, batch_id: int) -> float:
        """
        Gets the current available tonnage for a batch.
        
        Returns:
            Current tonnage in kg, or 0 if batch not found
        """
        batch = self.batch_repo.get_by_id(batch_id)
        if batch:
            return batch.current_tonnage or 0
        return 0

    def reserve_tonnage(self, batch_id: int, amount: float) -> bool:
        """
        Reserves (subtracts) tonnage from a batch for dispatch.
        Used by DispatchService when creating a load.
        
        Args:
            batch_id: ID of the batch
            amount: Amount to reserve in kg
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If insufficient stock or invalid amount
        """
        if amount <= 0:
            raise ValueError("La cantidad a reservar debe ser mayor a 0.")
        
        # The repository method will handle stock validation
        return self.batch_repo.update_current_tonnage(batch_id, amount)

    def return_tonnage(self, batch_id: int, amount: float) -> bool:
        """
        Returns (adds) tonnage to a batch (e.g., cancelled dispatch or weight adjustment).
        
        Args:
            batch_id: ID of the batch
            amount: Amount to return in kg
            
        Returns:
            True if successful
        """
        if amount <= 0:
            raise ValueError("La cantidad a devolver debe ser mayor a 0.")
        
        # Negative amount = add back to stock
        return self.batch_repo.update_current_tonnage(batch_id, -amount)

    def get_batches_by_facility(self, facility_id: int) -> List[Batch]:
        """
        Returns all batches for a facility, regardless of status.
        """
        return self.batch_repo.get_by_facility(facility_id)

    def get_batch_by_id(self, batch_id: int) -> Optional[Batch]:
        """
        Gets a batch by its ID.
        """
        return self.batch_repo.get_by_id(batch_id)

    def get_batch_by_code(self, batch_code: str) -> Optional[Batch]:
        """
        Gets a batch by its unique code.
        """
        return self.batch_repo.get_by_batch_code(batch_code)

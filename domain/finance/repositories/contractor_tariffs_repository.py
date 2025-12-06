from typing import Optional, List
from infrastructure.persistence.database_manager import DatabaseManager


class ContractorTariffsRepository:
    """
    Repository for querying the contractor_tariffs table.
    
    Handles retrieval of contractor cost tariffs with fuel indexing.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "contractor_tariffs"
    
    def get_active_tariff(
        self, 
        contractor_id: int, 
        vehicle_type: str
    ) -> Optional[dict]:
        """
        Returns the currently active tariff for a contractor and vehicle type.
        
        Active tariff is defined as valid_to IS NULL.
        
        Args:
            contractor_id: ID of the contractor
            vehicle_type: Vehicle classification ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')
            
        Returns:
            Dict with keys: id, contractor_id, vehicle_type, base_rate_uf,
                           min_weight_guaranteed, base_fuel_price, valid_from, valid_to
            None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, contractor_id, vehicle_type, 
                           base_rate as base_rate_uf,
                           min_weight_guaranteed, base_fuel_price,
                           valid_from, valid_to
                    FROM {self.table_name}
                    WHERE contractor_id = ? 
                      AND vehicle_type = ?
                      AND valid_to IS NULL
                    ORDER BY valid_from DESC
                    LIMIT 1""",
                (contractor_id, vehicle_type)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_active(self) -> List[dict]:
        """
        Returns all currently active tariffs (valid_to IS NULL).
        
        Useful for bulk operations and reporting.
        
        Returns:
            List of dicts with tariff data
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, contractor_id, vehicle_type, 
                           base_rate as base_rate_uf,
                           min_weight_guaranteed, base_fuel_price,
                           valid_from, valid_to,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE valid_to IS NULL
                    ORDER BY contractor_id, vehicle_type"""
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_by_contractor(self, contractor_id: int) -> List[dict]:
        """
        Returns all tariffs (active and historical) for a specific contractor.
        
        Args:
            contractor_id: ID of the contractor
            
        Returns:
            List of tariff dicts ordered by valid_from DESC
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, contractor_id, vehicle_type, 
                           base_rate as base_rate_uf,
                           min_weight_guaranteed, base_fuel_price,
                           valid_from, valid_to
                    FROM {self.table_name}
                    WHERE contractor_id = ?
                    ORDER BY valid_from DESC""",
                (contractor_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

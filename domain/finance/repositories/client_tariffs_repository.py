from typing import Optional, List
from infrastructure.persistence.database_manager import DatabaseManager


class ClientTariffsRepository:
    """
    Repository for querying the client_tariffs table.
    
    Handles retrieval of client billing tariffs (revenue side).
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "client_tariffs"
    
    def get_active_tariffs_by_client(self, client_id: int) -> List[dict]:
        """
        Returns all active tariffs for a specific client.
        
        Active tariffs are those with valid_to IS NULL.
        Typically returns 1-3 tariffs per client (TRANSPORTE, DISPOSICION, TRATAMIENTO).
        
        Args:
            client_id: ID of the client
            
        Returns:
            List of dicts with keys: id, client_id, concept, rate_uf,
                                    min_weight_guaranteed, valid_from, valid_to
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, client_id, concept, rate_uf,
                           min_weight_guaranteed, valid_from, valid_to
                    FROM {self.table_name}
                    WHERE client_id = ?
                      AND valid_to IS NULL
                    ORDER BY concept""",
                (client_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_active_tariff_by_concept(
        self, 
        client_id: int, 
        concept: str
    ) -> Optional[dict]:
        """
        Returns the active tariff for a specific client and billing concept.
        
        Args:
            client_id: ID of the client
            concept: Billing concept ('TRANSPORTE', 'TRATAMIENTO', 'DISPOSICION')
            
        Returns:
            Dict with tariff data, or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, client_id, concept, rate_uf,
                           min_weight_guaranteed, valid_from, valid_to
                    FROM {self.table_name}
                    WHERE client_id = ? 
                      AND concept = ?
                      AND valid_to IS NULL
                    ORDER BY valid_from DESC
                    LIMIT 1""",
                (client_id, concept)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_active(self) -> List[dict]:
        """
        Returns all currently active tariffs across all clients.
        
        Useful for bulk revenue calculations and reporting.
        
        Returns:
            List of dicts with tariff data
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, client_id, concept, rate_uf,
                           min_weight_guaranteed, valid_from, valid_to,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE valid_to IS NULL
                    ORDER BY client_id, concept"""
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

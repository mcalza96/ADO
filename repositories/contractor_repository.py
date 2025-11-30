from typing import List, Optional
from database.repository import BaseRepository
from models.masters.transport import Contractor
from database.db_manager import DatabaseManager


class ContractorRepository(BaseRepository[Contractor]):
    """
    Repository for Contractor entity.
    Handles all data access operations for transport contractors.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Contractor, "contractors")
    
    def get_all_active(self) -> List[Contractor]:
        """
        Returns all contractors ordered by name.
        """
        return self.get_all(order_by="name")
    
    def get_by_rut(self, rut: str) -> Optional[Contractor]:
        """
        Get a contractor by their RUT (Tax ID).
        Useful for validating duplicates.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE rut = ?", (rut,))
            row = cursor.fetchone()
            if row:
                return self.model_cls(**dict(row))
            return None

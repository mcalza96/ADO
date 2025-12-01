from typing import List, Optional
from database.repository import BaseRepository
from models.masters.client import Client
from database.db_manager import DatabaseManager


class ClientRepository(BaseRepository[Client]):
    """
    Repository for Client entity.
    Handles all data access operations for clients (biosolid generators).
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Client, "clients")
    
    def get_all_ordered(self) -> List[Client]:
        """
        Returns all clients ordered by name.
        """
        return self.get_all(order_by="name")
    
    def get_by_rut(self, rut: str) -> Optional[Client]:
        """
        Get a client by their RUT (Tax ID).
        Useful for validating duplicates.
        
        Args:
            rut: Client's RUT
            
        Returns:
            Client if found, None otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE rut = ?", (rut,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None

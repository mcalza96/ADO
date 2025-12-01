from typing import List, Optional
from database.repository import BaseRepository
from models.masters.container import Container
from database.db_manager import DatabaseManager


class ContainerRepository(BaseRepository[Container]):
    """
    Repository for Container entity.
    Handles all data access operations for Roll-off containers.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Container, "containers")
    
    def get_by_contractor(self, contractor_id: int, active_only: bool = True) -> List[Container]:
        """
        Get all containers for a specific contractor with contractor name.
        Performs JOIN with contractors table.
        
        Args:
            contractor_id: Contractor ID
            active_only: If True, only return active containers
        
        Returns:
            List of Container objects with contractor_name populated
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT c.*, ctr.name as contractor_name 
                FROM {self.table_name} c
                JOIN contractors ctr ON c.contractor_id = ctr.id
                WHERE c.contractor_id = ?
            """
            
            if active_only:
                query += " AND c.is_active = 1"
            
            query += " ORDER BY c.code"
            
            cursor.execute(query, (contractor_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_by_code(self, code: str) -> Optional[Container]:
        """
        Get a container by its unique code.
        Useful for validating duplicate codes.
        
        Args:
            code: Container code (e.g., "TOLVA-204")
            
        Returns:
            Container if found, None otherwise
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE code = ?",
                (code,)
            )
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None
    
    def get_all_active(self) -> List[Container]:
        """
        Get all active containers across all contractors with contractor name.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT c.*, ctr.name as contractor_name 
                FROM {self.table_name} c
                JOIN contractors ctr ON c.contractor_id = ctr.id
                WHERE c.is_active = 1 
                ORDER BY c.code
                """
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

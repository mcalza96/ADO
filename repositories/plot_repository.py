from typing import List
from database.repository import BaseRepository
from models.masters.location import Plot
from database.db_manager import DatabaseManager

class PlotRepository(BaseRepository[Plot]):
    """
    Repository for Plot entity (Parcelas).
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Plot, "plots")
    
    def get_by_site_id(self, site_id: int) -> List[Plot]:
        """
        Get all plots for a specific site.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE site_id = ? AND is_active = 1", (site_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

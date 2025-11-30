from typing import List, Optional
from database.repository import BaseRepository
from models.masters.location import Plot
from database.db_manager import DatabaseManager


class PlotRepository(BaseRepository[Plot]):
    """
    Repository for Plot entity (Agricultural sectors/parcels).
    Handles all data access operations for plot management.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Plot, "plots")
    
    def get_by_site(self, site_id: int) -> List[Plot]:
        """
        Get all active plots for a specific site.
        
        Args:
            site_id: ID of the site
            
        Returns:
            List of active plots belonging to the site
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE site_id = ? AND is_active = 1 ORDER BY name",
                (site_id,)
            )
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]
    
    def get_all_active(self) -> List[Plot]:
        """
        Get all active plots across all sites.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE is_active = 1 ORDER BY name"
            )
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]

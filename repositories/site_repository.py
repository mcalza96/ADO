from typing import Optional
from database.repository import BaseRepository
from database.db_manager import DatabaseManager
from models.masters.location import Site
from models.masters.disposal import Plot

class SiteRepository(BaseRepository[Site]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Site, "sites")

    def get_active_plot(self, site_id: int) -> Optional[Plot]:
        """
        Retrieves the currently active plot for a given site.
        Assumes a site has one active plot at a time for simplicity, 
        or returns the first one found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Assuming table name 'plots' and it has 'site_id' and 'is_active'
            cursor.execute("SELECT * FROM plots WHERE site_id = ? AND is_active = 1", (site_id,))
            row = cursor.fetchone()
            if row:
                return Plot(**dict(row))
            return None

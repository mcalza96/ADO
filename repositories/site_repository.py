from typing import List, Optional
from database.repository import BaseRepository
from models.masters.location import Site, Plot
from database.db_manager import DatabaseManager
from repositories.plot_repository import PlotRepository

class SiteRepository(BaseRepository[Site]):
    """
    Repository for Site entity (Granjas/Fundos).
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Site, "sites")
        # We initialize PlotRepository lazily or pass it? 
        # For simplicity, we can instantiate it here or use a separate query.
        # Ideally, we should avoid circular deps. PlotRepository depends on nothing but DB.
        self.plot_repository = PlotRepository(db_manager)
    
    def get_by_id(self, id: int, include_plots: bool = False) -> Optional[Site]:
        """
        Get a site by ID, optionally including its plots.
        """
        site = super().get_by_id(id)
        if site and include_plots:
            site.plots = self.plot_repository.get_by_site_id(site.id)
        return site

    def get_all_ordered(self) -> List[Site]:
        """
        Returns all sites ordered by name.
        """
        return self.get_all(order_by="name")

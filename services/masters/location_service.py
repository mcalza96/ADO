from typing import List, Optional
import streamlit as st
from models.masters.location import Site, Plot
from database.repository import BaseRepository

class LocationService:
    """
    Service for managing Sites and Plots (Location/Agronomy Masters).
    """
    
    def __init__(self, site_repo: BaseRepository[Site], plot_repo: BaseRepository[Plot]):
        self.site_repo = site_repo
        self.plot_repo = plot_repo

    def create_site(self, site: Site) -> Site:
        """
        Creates a new Site.
        """
        # Basic validation if needed
        # Invalidate cache
        st.cache_data.clear()
        return self.site_repo.add(site)

    def update_site(self, site: Site) -> Site:
        """
        Updates an existing Site.
        """
        # Invalidate cache
        st.cache_data.clear()
        return self.site_repo.update(site)
    
    def get_site(self, site_id: int, include_plots: bool = False) -> Optional[Site]:
        """
        Retrieves a site by ID.
        """
        return self.site_repo.get_by_id(site_id, include_plots=include_plots)

    @st.cache_data(ttl=3600)
    def get_all_sites(_self, active_only: bool = False) -> List[Site]:
        """
        Retrieves all sites, optionally filtering by active status.
        """
        sites = _self.site_repo.get_all_ordered()
        if active_only:
            return [s for s in sites if s.is_active]
        return sites

    def create_plot(self, plot: Plot) -> Plot:
        """
        Creates a new Plot with validations.
        """
        self._validate_plot(plot)
        return self.plot_repo.add(plot)

    def update_plot(self, plot: Plot) -> Plot:
        """
        Updates an existing Plot.
        """
        self._validate_plot(plot, is_update=True)
        return self.plot_repo.update(plot)
    
    def get_plots_by_site(self, site_id: int) -> List[Plot]:
        return self.plot_repo.get_all_filtered(site_id=site_id, is_active=1)

    def _validate_plot(self, plot: Plot, is_update: bool = False):
        """
        Validates plot business rules.
        """
        # 1. Area Positive
        if plot.area_acres <= 0:
            raise ValueError("El área de la parcela debe ser mayor a 0 acres.")

        # 2. Unicidad Local (Name unique within Site)
        existing_plots = self.plot_repo.get_all_filtered(site_id=plot.site_id, is_active=1)
        for p in existing_plots:
            if p.name.lower() == plot.name.lower():
                # If updating, allow same name if it's the same ID
                if is_update and p.id == plot.id:
                    continue
                raise ValueError(f"Ya existe una parcela con el nombre '{plot.name}' en este sitio.")

        # 3. Validation WKT (Basic)
        if plot.geometry_wkt:
            wkt = plot.geometry_wkt.strip().upper()
            if not (wkt.startswith("POLYGON") or wkt.startswith("MULTIPOLYGON")):
                raise ValueError("Formato de geometría inválido. Debe ser POLYGON o MULTIPOLYGON en formato WKT.")

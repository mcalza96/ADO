from typing import List, Optional
from models.masters.location import Site, Plot
from repositories.site_repository import SiteRepository
from repositories.plot_repository import PlotRepository

class LocationService:
    """
    Service for managing Sites and Plots (Location/Agronomy Masters).
    """
    
    def __init__(self, site_repo: SiteRepository, plot_repo: PlotRepository):
        self.site_repo = site_repo
        self.plot_repo = plot_repo

    def create_site(self, site: Site) -> Site:
        """
        Creates a new Site.
        """
        # Basic validation if needed
        return self.site_repo.add(site)

    def update_site(self, site: Site) -> Site:
        """
        Updates an existing Site.
        """
        return self.site_repo.update(site)
    
    def get_site(self, site_id: int, include_plots: bool = False) -> Optional[Site]:
        """
        Retrieves a site by ID.
        """
        return self.site_repo.get_by_id(site_id) # include_plots handled in repo? No, repo has custom method.
        # Wait, SiteRepository.get_by_id has include_plots param.
        # BaseRepository.get_by_id does NOT.
        # SiteRepository overrides it.
        return self.site_repo.get_by_id(site_id, include_plots=include_plots)

    def get_all_sites(self) -> List[Site]:
        """
        Retrieves all active sites.
        """
        return self.site_repo.get_all_ordered()

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
        return self.plot_repo.get_by_site_id(site_id)

    def _validate_plot(self, plot: Plot, is_update: bool = False):
        """
        Validates plot business rules.
        """
        # 1. Area Positive
        if plot.area_acres <= 0:
            raise ValueError("El área de la parcela debe ser mayor a 0 acres.")

        # 2. Unicidad Local (Name unique within Site)
        existing_plots = self.plot_repo.get_by_site_id(plot.site_id)
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

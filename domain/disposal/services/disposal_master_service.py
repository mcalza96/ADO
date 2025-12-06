from typing import List
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager
from infrastructure.persistence.generic_repository import BaseRepository
from domain.shared.entities.location import Plot
from domain.disposal.entities.disposal_method import SoilSample
from domain.disposal.entities.disposal_method import SoilSample
from domain.shared.services.compliance_validator import ComplianceValidator
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.entities.load import Load
from domain.logistics.entities.load_status import LoadStatus


class DisposalService:
    def __init__(self, db_manager: DatabaseManager):
        self.plot_repo = BaseRepository(db_manager, Plot, "plots")
        self.soil_repo = BaseRepository(db_manager, SoilSample, "soil_samples")
        self.load_repo = LoadRepository(db_manager)
        self.db_manager = db_manager

    def validate_application(self, site_id: int, biosolid_class: str) -> bool:
        """
        Validates if the site can accept the biosolid class.
        Uses Domain Logic.
        """
        # Get Site Type (Mocking logic or fetching from DB)
        # In a real scenario, we would fetch the Site entity and check its type.
        # For this MVP, let's query the site directly.
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Site not found")
            
            # We assume 'region' or a new field 'site_type' determines restrictions.
            # For MVP, let's assume if name contains "Parque" it's restricted.
            site_name = row['name']
            site_type = "Public Park" if "Parque" in site_name else "Agricultural"
            
            return ComplianceValidator.validate_class_restrictions(biosolid_class, site_type)

    # --- Plots ---
    def get_plots_by_site(self, site_id: int) -> List[Plot]:
        """Get all plots for a specific site."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM plots WHERE site_id = ? AND is_active = 1 ORDER BY name",
                (site_id,)
            )
            rows = cursor.fetchall()
            return [Plot(**dict(row)) for row in rows]

    def create_plot(self, plot: Plot) -> Plot:
        return self.plot_repo.add(plot)

    # --- Soil Samples ---
    def get_soil_samples_by_plot(self, plot_id: int) -> List[SoilSample]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM soil_samples WHERE plot_id = ? ORDER BY sampling_date DESC", (plot_id,))
            rows = cursor.fetchall()
            return [SoilSample(**dict(row)) for row in rows]

    def create_soil_sample(self, sample: SoilSample) -> SoilSample:
        """Renamed from add_soil_sample for consistency"""
        return self.soil_repo.add(sample)

    # --- Loads / Reception ---
    def get_in_transit_loads_by_destination_site(self, site_id: int) -> List[Load]:
        """
        Get loads in transit (EN_ROUTE_DESTINATION) heading to a disposal site.
        
        Used by disposal reception to show incoming trucks.
        
        Args:
            site_id: ID of the destination site
            
        Returns:
            List of loads in transit to the site
        """
        return self.load_repo.get_in_transit_loads_by_destination_site(site_id)

    def get_pending_disposal_loads(self, site_id: int) -> List[Load]:
        """
        Get loads ready for disposal (AT_DESTINATION status) at a site.
        
        Used by disposal field view to show loads ready for incorporation.
        
        Args:
            site_id: ID of the destination site
            
        Returns:
            List of loads ready for disposal
        """
        loads = self.load_repo.get_by_status(LoadStatus.AT_DESTINATION.value)
        return [l for l in loads if l.destination_site_id == site_id]

    def register_arrival(self, load_id: int, ph: float, observation: str = None) -> bool:
        """
        Register arrival of a load at the disposal site.
        
        Changes status from EN_ROUTE_DESTINATION to AT_DESTINATION.
        Only captures pH verification - other data comes from transport module.
        
        Args:
            load_id: ID of the load
            ph: pH verification measured at reception
            observation: Optional observations
            
        Returns:
            True if successful
        """
        from datetime import datetime
        from domain.logistics.entities.load_status import LoadStatus
        
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
        
        # Aceptar tanto el nuevo status como el legacy
        valid_statuses = [LoadStatus.EN_ROUTE_DESTINATION.value, 'Dispatched', 'InTransit']
        if load.status not in valid_statuses:
            raise ValueError(f"Load must be in transit. Current: {load.status}")
        
        # Actualizar pH de verificación y observaciones
        load.quality_ph = ph
        if observation:
            load.reception_observations = observation
        
        # Cambiar status y registrar llegada
        load.arrival_time = datetime.now()
        load.status = LoadStatus.AT_DESTINATION.value
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

    def execute_disposal(self, load_id: int, plot_id: int) -> bool:
        """
        Complete the disposal of a load to a specific plot.
        
        Changes status from AT_DESTINATION to COMPLETED.
        
        Args:
            load_id: ID of the load
            plot_id: ID of the plot/sector where the load is disposed
            
        Returns:
            True if successful
        """
        load = self.load_repo.get_by_id(load_id)
        if not load:
            raise ValueError(f"Load {load_id} not found")
        
        if load.status != LoadStatus.AT_DESTINATION.value:
            raise ValueError(f"Load must be at destination. Current: {load.status}")
        
        # Verificar que la parcela existe y pertenece al predio
        plot = self.plot_repo.get_by_id(plot_id)
        if not plot:
            raise ValueError(f"Plot {plot_id} not found")
        
        if plot.site_id != load.destination_site_id:
            raise ValueError("Plot does not belong to the load's destination site")
        
        # Actualizar la carga con la parcela de destino y completar
        load.destination_plot_id = plot_id
        load.disposal_time = datetime.now()
        load.status = LoadStatus.COMPLETED.value
        load.updated_at = datetime.now()
        
        return self.load_repo.update(load)

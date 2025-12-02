from typing import List
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.location import Plot
from database.repository import BaseRepository
from models.masters.location import Plot
from models.masters.disposal import SoilSample
from domain.compliance.validator import ComplianceValidator


class DisposalService:
    def __init__(self, db_manager: DatabaseManager):
        self.plot_repo = BaseRepository(db_manager, Plot, "plots")
        self.soil_repo = BaseRepository(db_manager, SoilSample, "soil_samples")
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
        return self.plot_repo.get_by_site_id(site_id)

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


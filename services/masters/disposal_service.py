from typing import List
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.disposal import Plot, SoilSample

class DisposalService:
    def __init__(self, db_manager: DatabaseManager):
        self.plot_repo = BaseRepository(db_manager, Plot, "plots")
        self.soil_repo = BaseRepository(db_manager, SoilSample, "soil_samples")
        self.db_manager = db_manager

    # --- Plots ---
    def get_plots_by_site(self, site_id: int) -> List[Plot]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plots WHERE site_id = ? AND is_active = 1", (site_id,))
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

    def add_soil_sample(self, sample: SoilSample) -> SoilSample:
        return self.soil_repo.add(sample)

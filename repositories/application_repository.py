from typing import List, Optional
from datetime import date
from database.repository import BaseRepository
from database.db_manager import DatabaseManager
from models.agronomy.application import NitrogenApplication

class ApplicationRepository(BaseRepository[NitrogenApplication]):
    """
    Repository for tracking nitrogen applications to sites.
    Manages the 'nitrogen_applications' table.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, NitrogenApplication, "nitrogen_applications")

    def get_year_total_nitrogen(self, site_id: int, year: int) -> float:
        """
        Calculates the total nitrogen applied to a site in a specific year.
        
        Args:
            site_id: ID of the site
            year: Year to calculate total for
            
        Returns:
            Total nitrogen in kg
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            cursor.execute(
                f"""
                SELECT SUM(nitrogen_applied_kg) as total 
                FROM {self.table_name} 
                WHERE site_id = ? AND application_date BETWEEN ? AND ?
                """,
                (site_id, start_date, end_date)
            )
            row = cursor.fetchone()
            return row['total'] if row and row['total'] else 0.0

import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from database.db_manager import DatabaseManager

class ReportingRepository:
    """
    Repository for executing reporting-related SQL queries.
    Separates SQL logic from the ReportingService.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_full_traceability(self) -> pd.DataFrame:
        """
        Fetches data from the view_full_traceability view.
        """
        query = "SELECT * FROM view_full_traceability WHERE 1=1"
        with self.db_manager as conn:
            return pd.read_sql_query(query, conn)

    def get_fleet_monitoring_data(self) -> pd.DataFrame:
        """
        Fetches active loads for fleet monitoring.
        """
        query = """
            SELECT 
                l.id as load_id,
                l.status,
                l.dispatch_time,
                l.arrival_time,
                l.weight_gross_reception as weight_arrival,
                l.weight_net,
                l.ticket_number,
                l.guide_number,
                v.license_plate,
                d.name as driver_name,
                f.name as facility_name,
                s.name as site_name,
                l.destination_site_id
            FROM loads l
            LEFT JOIN vehicles v ON l.vehicle_id = v.id
            LEFT JOIN drivers d ON l.driver_id = d.id
            LEFT JOIN facilities f ON l.origin_facility_id = f.id
            LEFT JOIN sites s ON l.destination_site_id = s.id
            WHERE l.status IN ('Dispatched', 'Arrived')
            ORDER BY l.dispatch_time DESC
        """
        with self.db_manager as conn:
            return pd.read_sql_query(query, conn)

    def get_site_plots_agronomy(self, site_id: int) -> pd.DataFrame:
        """
        Fetches plot agronomy data for a specific site.
        """
        query_plots = """
            SELECT 
                p.id, p.name, p.area_hectares,
                (SELECT SUM(nitrogen_load_applied) FROM applications a WHERE a.plot_id = p.id) as current_n
            FROM plots p
            WHERE p.site_id = ?
        """
        with self.db_manager as conn:
            return pd.read_sql_query(query_plots, conn, params=(site_id,))

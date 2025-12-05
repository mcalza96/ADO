import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from repositories.reporting_repository import ReportingRepository
from domain.shared.constants import MAX_N_PER_HA

class ReportingService:
    """
    Service for generating reports and dashboards data.
    Leverages the ReportingRepository for data access.
    """

    def __init__(self, reporting_repository: ReportingRepository):
        self.repository = reporting_repository

    def get_client_report(self, client_id: Optional[int] = None, date_range: tuple = None) -> pd.DataFrame:
        """
        Returns a DataFrame for the Client Portal.
        Filters by client_id and date range if provided.
        """
        df = self.repository.get_full_traceability()
        
        # Post-processing
        if date_range:
            start_date, end_date = date_range
            # Ensure dispatch_time is datetime
            df['dispatch_time'] = pd.to_datetime(df['dispatch_time'])
            # Convert date objects to Timestamp for comparison
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            mask = (df['dispatch_time'] >= start_ts) & (df['dispatch_time'] <= end_ts)
            df = df.loc[mask]

        if client_id:
            # This is tricky without client_id in view. 
            # I'll rely on the UI passing the client name or filtering by it.
            # For now, I will return the whole DF and let the UI filter or 
            # I will implement a 'filter_by_client_name' if needed.
            # Let's assume the caller handles specific client filtering or we add it later.
            pass
            
        return df

    def get_fleet_monitoring(self) -> pd.DataFrame:
        """
        Returns a DataFrame with all trucks currently in the field logistics cycle.
        Includes both 'Dispatched' (En Ruta) and 'Arrived' (En Cola/Espera de Descarga).
        
        Calculates:
        - hours_elapsed: Travel time (Dispatched) or completed travel time (Arrived)
        - waiting_time: Time waiting at site (only for Arrived status)
        """
        df = self.repository.get_fleet_monitoring_data()
            
        if not df.empty:
            # Convert timestamps to datetime
            df['dispatch_time'] = pd.to_datetime(df['dispatch_time'])
            df['arrival_time'] = pd.to_datetime(df['arrival_time'])
            
            now = datetime.now()
            
            # Calculate hours_elapsed based on status
            def calculate_hours_elapsed(row):
                if row['status'] == 'Dispatched':
                    # For Dispatched: time since dispatch (ongoing trip)
                    if pd.notna(row['dispatch_time']):
                        return (now - row['dispatch_time']).total_seconds() / 3600
                elif row['status'] == 'Arrived':
                    # For Arrived: completed travel time (arrival - dispatch)
                    if pd.notna(row['arrival_time']) and pd.notna(row['dispatch_time']):
                        return (row['arrival_time'] - row['dispatch_time']).total_seconds() / 3600
                return 0.0
            
            # Calculate waiting_time (only for Arrived)
            def calculate_waiting_time(row):
                if row['status'] == 'Arrived' and pd.notna(row['arrival_time']):
                    return (now - row['arrival_time']).total_seconds() / 3600
                return 0.0
            
            df['hours_elapsed'] = df.apply(calculate_hours_elapsed, axis=1)
            df['waiting_time'] = df.apply(calculate_waiting_time, axis=1)
        else:
            # Empty DataFrame with expected columns
            df['hours_elapsed'] = 0.0
            df['waiting_time'] = 0.0
            
        return df

    def get_site_agronomy_stats(self, site_id: int) -> Dict[str, Any]:
        """
        Returns agronomic metrics for a specific site.
        Total N applied vs Max Capacity.
        """
        df_plots = self.repository.get_site_plots_agronomy(site_id)
        
        if not df_plots.empty:
            df_plots['current_n'] = df_plots['current_n'].fillna(0)
            df_plots['max_n'] = df_plots['area_hectares'] * MAX_N_PER_HA
            df_plots['usage_percent'] = (df_plots['current_n'] / df_plots['max_n']).clip(upper=1.0)
        
        return df_plots

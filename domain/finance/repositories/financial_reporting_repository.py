from typing import List, Dict, Any, Optional
from datetime import datetime
from infrastructure.persistence.database_manager import DatabaseManager

class FinancialReportingRepository:
    """
    Repository for financial reporting data access.
    Encapsulates SQL queries used in financial reports.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_vehicle_type(self, vehicle_id: int) -> str:
        """Get vehicle type by ID."""
        if not vehicle_id:
            return 'AMPLIROLL'
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT type FROM vehicles WHERE id = ?", (vehicle_id,))
                row = cursor.fetchone()
                if row and row['type']:
                    return row['type'].upper()
        except Exception:
            pass
        return 'AMPLIROLL'

    def fetch_loads_in_cycle(self, cycle_start: datetime, cycle_end: datetime) -> List[Dict[str, Any]]:
        """Fetch completed loads within a billing cycle."""
        query = """
            SELECT 
                l.id,
                l.manifest_code as manifest_number,
                l.vehicle_id,
                f_origin.client_id,
                l.status,
                l.scheduled_date,
                l.net_weight / 1000.0 as net_weight_tons,
                l.origin_facility_id,
                l.origin_treatment_plant_id,
                l.destination_site_id,
                l.destination_treatment_plant_id,
                v.license_plate as vehicle_name,
                c.name as client_name,
                COALESCE(f_origin.name, tp_origin.name, 'N/A') as origin_name,
                COALESCE(s.name, tp_dest.name, 'N/A') as destination_name
            FROM loads l
            LEFT JOIN vehicles v ON l.vehicle_id = v.id
            LEFT JOIN facilities f_origin ON l.origin_facility_id = f_origin.id
            LEFT JOIN clients c ON f_origin.client_id = c.id
            LEFT JOIN treatment_plants tp_origin ON l.origin_treatment_plant_id = tp_origin.id
            LEFT JOIN sites s ON l.destination_site_id = s.id
            LEFT JOIN treatment_plants tp_dest ON l.destination_treatment_plant_id = tp_dest.id
            WHERE l.status IN ('ARRIVED', 'COMPLETED')
              AND l.scheduled_date BETWEEN ? AND ?
            ORDER BY l.scheduled_date ASC
        """
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, (cycle_start.isoformat(), cycle_end.isoformat()))
            return [dict(row) for row in cursor.fetchall()]

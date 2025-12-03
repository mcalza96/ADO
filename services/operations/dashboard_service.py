from typing import Dict, Optional
from database.db_manager import DatabaseManager
from domain.shared.base_service import BaseService
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator
from domain.logistics.entities.load import Load

class DashboardService(BaseService):
    """Service for dashboard operations and statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.manifest_generator = PdfManifestGenerator()

    def get_stats(self) -> Dict:
        """Get operational statistics for dashboard display."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Count Clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            
            # Count Active Loads (Scheduled, InTransit, Waiting)
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status IN ('Scheduled', 'InTransit', 'Waiting')")
            active_loads = cursor.fetchone()[0]
            
            # Count Completed Loads Today (Disposed)
            try:
                cursor.execute("SELECT COUNT(*) FROM loads WHERE status = 'Disposed' AND date(disposal_time) = date('now')")
                completed_today = cursor.fetchone()[0]
            except:
                # Fallback if disposal_time column doesn't exist
                cursor.execute("SELECT COUNT(*) FROM loads WHERE status = 'Disposed' AND date(created_at) = date('now')")
                completed_today = cursor.fetchone()[0]
            
            # Total Tonnage Today
            try:
                cursor.execute("SELECT SUM(COALESCE(net_weight, (COALESCE(gross_weight, 0) - COALESCE(tare_weight, 0)))) FROM loads WHERE status IN ('Disposed', 'COMPLETED') AND date(COALESCE(disposal_time, updated_at)) = date('now')")
                tonnage_today = cursor.fetchone()[0] or 0.0
            except Exception as e:
                # Fallback in case of any error
                tonnage_today = 0.0
            
            return {
                "clients": client_count,
                "active_loads": active_loads,
                "completed_today": completed_today,
                "tonnage_today": tonnage_today
            }

    def get_load_traceability(self, load_id: int) -> Optional[Dict]:
        """Get full traceability information for a specific load."""
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, 
                       f.name as origin_name, 
                       s.name as dest_name,
                       d.name as driver_name,
                       v.license_plate as vehicle_plate
                FROM loads l
                LEFT JOIN facilities f ON l.origin_facility_id = f.id
                LEFT JOIN sites s ON l.destination_site_id = s.id
                LEFT JOIN drivers d ON l.driver_id = d.id
                LEFT JOIN vehicles v ON l.vehicle_id = v.id
                WHERE l.id = ?
            """, (load_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def generate_manifest(self, load_dict: dict) -> bytes:
        """Generate PDF manifest for a load."""
        # Convert dict back to Load object for the generator (partial reconstruction)
        # In a real app, we might fetch the full object via ORM
        load_obj = Load(**{k: v for k, v in load_dict.items() if k in Load.__annotations__})
        return self.manifest_generator.generate(load_obj, load_dict)

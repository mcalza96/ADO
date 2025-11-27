import streamlit as st
from database.db_manager import DatabaseManager
from services.base_service import BaseService

class DashboardService(BaseService):
    def get_stats(self):
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Count Clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            
            # Count Active Loads (Scheduled or InTransit)
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status IN ('Scheduled', 'InTransit')")
            active_loads = cursor.fetchone()[0]
            
            # Count Completed Loads Today
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status = 'Delivered' AND date(arrival_time) = date('now')")
            completed_today = cursor.fetchone()[0]
            
            # Total Tonnage Today
            cursor.execute("SELECT SUM(weight_net) FROM loads WHERE status = 'Delivered' AND date(arrival_time) = date('now')")
            tonnage_today = cursor.fetchone()[0] or 0.0
            
            return {
                "clients": client_count,
                "active_loads": active_loads,
                "completed_today": completed_today,
                "tonnage_today": tonnage_today
            }

def dashboard_page():
    st.title("Dashboard Operativo")
    st.markdown("### Resumen General")
    
    db = DatabaseManager()
    service = DashboardService(db)
    stats = service.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Clientes", stats["clients"])
    with col2:
        st.metric("Cargas Activas", stats["active_loads"])
    with col3:
        st.metric("Viajes Hoy", stats["completed_today"])
    with col4:
        st.metric("Toneladas Hoy", f"{stats['tonnage_today'] / 1000:.1f} t")
    
    st.divider()
    
    st.info("Seleccione un módulo del menú lateral para comenzar a operar.")

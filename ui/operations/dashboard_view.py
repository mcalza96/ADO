import streamlit as st
from database.db_manager import DatabaseManager
from services.base_service import BaseService
from infrastructure.reporting.pdf_manifest_generator import PdfManifestGenerator
from models.operations.load import Load

class DashboardService(BaseService):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.manifest_generator = PdfManifestGenerator()

    def get_stats(self):
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Count Clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            
            # Count Active Loads (Scheduled, InTransit, Waiting)
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status IN ('Scheduled', 'InTransit', 'Waiting')")
            active_loads = cursor.fetchone()[0]
            
            # Count Completed Loads Today (Disposed)
            cursor.execute("SELECT COUNT(*) FROM loads WHERE status = 'Disposed' AND date(disposal_time) = date('now')")
            completed_today = cursor.fetchone()[0]
            
            # Total Tonnage Today
            cursor.execute("SELECT SUM(weight_net) FROM loads WHERE status = 'Disposed' AND date(disposal_time) = date('now')")
            tonnage_today = cursor.fetchone()[0] or 0.0
            
            return {
                "clients": client_count,
                "active_loads": active_loads,
                "completed_today": completed_today,
                "tonnage_today": tonnage_today
            }

    def get_load_traceability(self, load_id: int):
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
        # Convert dict back to Load object for the generator (partial reconstruction)
        # In a real app, we might fetch the full object via ORM
        load_obj = Load(**{k: v for k, v in load_dict.items() if k in Load.__annotations__})
        return self.manifest_generator.generate(load_obj, load_dict)

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
        st.metric("Dispuestas Hoy", stats["completed_today"])
    with col4:
        st.metric("Toneladas Hoy", f"{stats['tonnage_today'] / 1000:.1f} t")
    
    st.divider()
    
    st.subheader("🔍 Trazabilidad de Carga")
    search_id = st.number_input("Buscar por ID de Carga", min_value=1, value=1)
    if st.button("Buscar"):
        load = service.get_load_traceability(search_id)
        if load:
            st.markdown(f"#### Carga #{load['id']} - Estado: **{load['status']}**")
            
            # Timeline
            steps = []
            if load['requested_date']: steps.append(f"📅 Solicitado: {load['requested_date']}")
            if load['scheduled_date']: steps.append(f"🗓️ Programado: {load['scheduled_date']}")
            if load['dispatch_time']: steps.append(f"🚛 Despachado: {load['dispatch_time']}")
            if load['arrival_time']: steps.append(f"🚧 En Portería: {load['arrival_time']}")
            if load['disposal_time']: steps.append(f"✅ Dispuesto: {load['disposal_time']}")
            
            st.code(" -> ".join(steps))
            
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Origen:** {load['origin_name']}")
                st.write(f"**Destino:** {load['dest_name']}")
                st.write(f"**Transporte:** {load['driver_name']} ({load['vehicle_plate']})")
            
            with c2:
                st.write(f"**Peso Neto:** {load['weight_net']} kg")
                if load['disposal_coordinates']:
                    st.write(f"**GPS Disposición:** `{load['disposal_coordinates']}`")
                if load['treatment_facility_id']:
                    st.write(f"**Tratamiento Intermedio:** ID {load['treatment_facility_id']}")
            
            # PDF Download Button
            if load['status'] == 'Disposed':
                st.divider()
                try:
                    pdf_bytes = service.generate_manifest(load)
                    st.download_button(
                        label="📥 Descargar Manifiesto de Carga (PDF)",
                        data=pdf_bytes,
                        file_name=f"Manifiesto_Carga_{load['id']}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error al generar PDF: {e}")
            else:
                st.info("El Manifiesto de Carga estará disponible una vez que la carga sea dispuesta.")
                
        else:
            st.error("Carga no encontrada.")
            
    st.divider()
    st.info("Seleccione un módulo del menú lateral para comenzar a operar.")

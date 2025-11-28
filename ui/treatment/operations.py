import streamlit as st
from database.db_manager import DatabaseManager
from services.masters.treatment_plant_service import TreatmentPlantService
from services.operations.treatment_reception import TreatmentReceptionService
from ui.treatment.ds4_monitoring import ds4_monitoring_view
from ui.styles import apply_industrial_style
import datetime

def treatment_operations_page():
    apply_industrial_style()
    st.title("🏭 Operaciones de Tratamiento")
    
    db = DatabaseManager()
    plant_service = TreatmentPlantService(db)
    reception_service = TreatmentReceptionService(db)
    
    # 1. Context Selection (Plant)
    plants = plant_service.get_all_plants()
    if not plants:
        st.warning("No hay plantas de tratamiento configuradas.")
        return
        
    p_opts = {p.name: p.id for p in plants}
    sel_plant_name = st.selectbox("Seleccione Planta de Trabajo", list(p_opts.keys()))
    plant_id = p_opts[sel_plant_name]
    
    st.divider()
    
    # TABS
    tab_reception, tab_ds4 = st.tabs(["📥 Recepción de Lodos", "🧪 Proceso DS4 (Salida)"])
    
    with tab_reception:
        st.subheader("Bandeja de Entrada (Descargas Pendientes)")
        
        if st.button("🔄 Actualizar Bandeja"):
            st.rerun()
            
        pending = reception_service.get_pending_reception_loads(plant_id)
        
        if not pending:
            st.info("No hay cargas pendientes de recepción técnica.")
        else:
            st.success(f"Hay {len(pending)} cargas esperando recepción.")
            
            for load in pending:
                with st.expander(f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - {load.weight_net} kg", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Ticket:** {load.ticket_number}")
                        st.markdown(f"**Llegada:** {load.arrival_time}")
                    with c2:
                        st.markdown(f"**Origen ID:** {load.origin_facility_id}")
                    with c3:
                        st.markdown(f"**Estado:** {load.status}")

                    st.divider()
                    st.markdown("#### Registro de Recepción Técnica")
                    
                    with st.form(f"reception_form_{load.id}"):
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            rec_time = st.time_input("Hora Ingreso Real", datetime.datetime.now().time())
                        with col_t2:
                            dis_time = st.time_input("Hora Descarga Foso", datetime.datetime.now().time())
                        
                        st.markdown("##### Variables de Calidad")
                        col_q1, col_q2 = st.columns(2)
                        with col_q1:
                            ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1, value=7.0)
                        with col_q2:
                            humidity = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1, value=80.0)
                        
                        if st.form_submit_button("✅ Confirmar Recepción"):
                            try:
                                # Combine with today's date for MVP simplicity, or use load date logic
                                today = datetime.date.today()
                                rec_dt = datetime.datetime.combine(today, rec_time)
                                dis_dt = datetime.datetime.combine(today, dis_time)
                                
                                reception_service.execute_reception(load.id, rec_dt, dis_dt, ph, humidity)
                                st.success(f"Carga #{load.id} recibida. Lote listo para proceso.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    with tab_ds4:
        ds4_monitoring_view(plant_id)


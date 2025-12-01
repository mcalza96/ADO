import streamlit as st
from container import get_container

def dashboard_page():
    st.title("Dashboard Operativo")
    st.markdown("### Resumen General")
    
    services = get_container()
    dashboard_service = services.dashboard_service
    stats = dashboard_service.get_stats()
    
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
        load = dashboard_service.get_load_traceability(search_id)
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
                    pdf_bytes = dashboard_service.generate_manifest(load)
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

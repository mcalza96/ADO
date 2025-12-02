import streamlit as st
import datetime
from domain.shared.dtos import AssignmentRequest
from ui.constants import DestinationType

def render_assignment_sidebar(selected_load_ids, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service):
    """
    Renderiza el formulario de asignación y retorna los datos si se confirma.
    """
    st.sidebar.header(f"Asignando {len(selected_load_ids)} Cargas")
    st.sidebar.markdown(f"**IDs Seleccionados:** {', '.join(map(str, selected_load_ids))}")
    
    with st.sidebar.form("assignment_form"):
        st.subheader("Recursos")
        
        # 1. Contractor & Driver
        contractors = contractor_service.get_all_contractors()
        c_opts = {c.name: c.id for c in contractors}
        sel_c = st.selectbox("Transportista", list(c_opts.keys()))
        
        driver_id = None
        vehicle_id = None
        
        if sel_c:
            c_id = c_opts[sel_c]
            drivers = driver_service.get_drivers_by_contractor(c_id)
            d_opts = {d.name: d.id for d in drivers}
            sel_d = st.selectbox("Conductor", list(d_opts.keys()))
            if sel_d: driver_id = d_opts[sel_d]
            
            vehicles = vehicle_service.get_vehicles_by_contractor(c_id)
            v_opts = {f"{v.license_plate} ({v.type})": v.id for v in vehicles}
            sel_v = st.selectbox("Vehículo", list(v_opts.keys()))
            if sel_v: vehicle_id = v_opts[sel_v]
        
        st.subheader("Destino")
        dest_type_label = st.radio("Tipo Destino", DestinationType.get_labels())
        dest_type = DestinationType.from_label(dest_type_label)
        
        site_id = None
        plant_id = None
        
        if dest_type == DestinationType.FIELD_SITE:
            sites = location_service.get_all_sites(active_only=True)
            s_opts = {s.name: s.id for s in sites}
            sel_s = st.selectbox("Predio Destino", list(s_opts.keys()))
            if sel_s: site_id = s_opts[sel_s]
        else:
            plants = treatment_plant_service.get_all()
            p_opts = {p.name: p.id for p in plants}
            sel_p = st.selectbox("Planta Destino", list(p_opts.keys()))
            if sel_p: plant_id = p_opts[sel_p]
            
        scheduled_date = st.date_input("Fecha Programada", datetime.date.today())
        
        if st.form_submit_button("💾 Confirmar Asignación"):
            return AssignmentRequest(
                load_ids=selected_load_ids,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                scheduled_date=scheduled_date,
                site_id=site_id,
                treatment_plant_id=plant_id
            )
    return None

import streamlit as st
import datetime
from domain.shared.dtos import AssignmentRequest
from domain.logistics.entities.vehicle import VehicleType
from ui.constants import DestinationType


def _filter_vehicles_by_allowed_types(vehicles, allowed_vehicle_types: str):
    """
    Filtra vehículos según los tipos permitidos por el destino.
    
    Args:
        vehicles: Lista de vehículos
        allowed_vehicle_types: CSV de tipos permitidos (ej: "BATEA,AMPLIROLL")
    
    Returns:
        Lista filtrada de vehículos compatibles
    """
    if not allowed_vehicle_types:
        return vehicles  # Sin restricción = todos permitidos
    
    allowed_types = VehicleType.from_csv(allowed_vehicle_types)
    allowed_values = [t.value for t in allowed_types]
    
    return [v for v in vehicles if v.type in allowed_values]


def render_assignment_form(selected_load_ids, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service, origin_allowed_vehicle_types=None):
    """
    Renderiza el formulario de asignación inline (dentro del contenido principal).
    Retorna AssignmentRequest si se confirma, None en caso contrario.
    
    Args:
        origin_allowed_vehicle_types: CSV de tipos de vehículos permitidos por el origen (facility).
                                      Si es None, no hay restricción.
    """
    st.markdown("---")
    st.subheader(f"📋 Asignando {len(selected_load_ids)} Cargas")
    st.caption(f"IDs Seleccionados: {', '.join(map(str, selected_load_ids))}")
    
    # === SECCIÓN 1: Destino ===
    st.markdown("**📍 Destino**")
    col_dest_type, col_dest_select = st.columns([1, 2])
    
    site_id = None
    plant_id = None
    
    with col_dest_type:
        dest_type_label = st.radio(
            "Tipo Destino", 
            DestinationType.get_labels(), 
            horizontal=True,
            key="assignment_dest_type"
        )
    dest_type = DestinationType.from_label(dest_type_label)
    
    with col_dest_select:
        if dest_type == DestinationType.FIELD_SITE:
            sites = location_service.get_all_sites(active_only=True)
            s_opts = {s.name: s.id for s in sites}
            if s_opts:
                sel_s = st.selectbox("Predio Destino", list(s_opts.keys()), key="assignment_site")
                if sel_s: 
                    site_id = s_opts[sel_s]
        else:
            plants = treatment_plant_service.get_all()
            p_opts = {p.name: p.id for p in plants}
            if p_opts:
                sel_p = st.selectbox("Planta Destino", list(p_opts.keys()), key="assignment_plant")
                if sel_p: 
                    plant_id = p_opts[sel_p]
    
    # === SECCIÓN 2: Transportista y Vehículo ===
    st.markdown("**🚛 Recursos**")
    
    # Mostrar restricción de vehículos del origen si existe
    if origin_allowed_vehicle_types:
        st.info(f"🏭 El origen solo permite vehículos tipo: **{origin_allowed_vehicle_types}**")
    
    col_contractor, col_driver, col_vehicle = st.columns(3)
    
    driver_id = None
    vehicle_id = None
    contractor_id = None
    
    contractors = contractor_service.get_all_contractors()
    c_opts = {c.name: c.id for c in contractors}
    
    with col_contractor:
        if not c_opts:
            st.warning("No hay transportistas")
        else:
            sel_c = st.selectbox("Transportista", list(c_opts.keys()), key="assignment_contractor")
            if sel_c:
                contractor_id = c_opts[sel_c]
    
    with col_driver:
        if contractor_id:
            drivers = driver_service.get_drivers_by_contractor(contractor_id)
            d_opts = {d.name: d.id for d in drivers}
            if d_opts:
                sel_d = st.selectbox("Conductor", list(d_opts.keys()), key="assignment_driver")
                if sel_d: 
                    driver_id = d_opts[sel_d]
            else:
                st.warning("Sin conductores")
    
    with col_vehicle:
        if contractor_id:
            all_vehicles = vehicle_service.get_vehicles_by_contractor(contractor_id)
            # Filtrar por restricción del ORIGEN (facility)
            vehicles = _filter_vehicles_by_allowed_types(all_vehicles, origin_allowed_vehicle_types)
            
            if not vehicles and all_vehicles:
                st.warning(f"⚠️ Sin vehículos autorizados para este origen ({origin_allowed_vehicle_types})")
            elif vehicles:
                v_opts = {f"{v.license_plate} ({v.type})": v.id for v in vehicles}
                sel_v = st.selectbox("Vehículo", list(v_opts.keys()), key="assignment_vehicle")
                if sel_v: 
                    vehicle_id = v_opts[sel_v]
            else:
                st.warning("Sin vehículos")
    
    # === SECCIÓN 3: Programación y Confirmación (dentro del form) ===
    with st.form("assignment_form"):
        st.markdown("**🗓️ Programación**")
        col_date, col_time, col_btn = st.columns([1, 1, 1])
        
        with col_date:
            scheduled_date = st.date_input("Fecha Programada", datetime.date.today())
        with col_time:
            scheduled_time = st.time_input("Hora de Retiro", datetime.time(8, 0))
        with col_btn:
            st.markdown("&nbsp;")  # Espaciador
            submit = st.form_submit_button("💾 Confirmar Asignación", width="stretch", type="primary")
        
        if submit:
            # Validaciones
            if not driver_id:
                st.error("Debe seleccionar un conductor")
                return None
            if not vehicle_id:
                st.error("Debe seleccionar un vehículo")
                return None
            if dest_type == DestinationType.FIELD_SITE and not site_id:
                st.error("Debe seleccionar un predio destino")
                return None
            if dest_type == DestinationType.TREATMENT_PLANT and not plant_id:
                st.error("Debe seleccionar una planta destino")
                return None
                
            return AssignmentRequest(
                load_ids=selected_load_ids,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                site_id=site_id,
                treatment_plant_id=plant_id
            )
    return None

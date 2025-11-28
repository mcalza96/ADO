import streamlit as st
import datetime
from database.db_manager import DatabaseManager
from services.operations_service import OperationsService
from services.masters.transport_service import TransportService
from services.masters.location_service import LocationService
from services.masters.disposal_service import DisposalService
from services.masters.treatment_plant_service import TreatmentPlantService

def planning_page():
    st.title("🗓️ Planificación de Retiros")
    
    db = DatabaseManager()
    ops_service = OperationsService(db)
    transport_service = TransportService(db)
    location_service = LocationService(db)
    treatment_plant_service = TreatmentPlantService(db)
    
    # 1. Fetch Requested Loads
    requested_loads = ops_service.get_loads_by_status('Requested')
    
    if not requested_loads:
        st.info("No hay solicitudes pendientes de planificación.")
        return
        
    st.write(f"Pendientes: {len(requested_loads)}")
    
    # 2. Planning Interface
    for load in requested_loads:
        req_date_str = load.requested_date if load.requested_date else "Sin fecha"
        # Resolve origin name (facility or treatment plant) to show readable text
        if load.origin_facility_id:
            fac = location_service.get_facility_by_id(load.origin_facility_id)
            origin_name = fac.name if (fac and getattr(fac, 'name', None)) else f"ID: {load.origin_facility_id}"
        elif load.origin_treatment_plant_id:
            plant = treatment_plant_service.get_plant_by_id(load.origin_treatment_plant_id)
            origin_name = plant.name if (plant and getattr(plant, 'name', None)) else f"Plant ID: {load.origin_treatment_plant_id}"
        else:
            origin_name = "Origen desconocido"
        with st.expander(f"Solicitud #{load.id} - Origen: {origin_name} - Para: {req_date_str}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Transporte")
                contractors = transport_service.get_all_contractors()
                c_opts = {c.name: c.id for c in contractors}
                sel_c = st.selectbox(f"Transportista #{load.id}", list(c_opts.keys()), key=f"c_{load.id}")
                
                sel_d = None
                sel_v = None
                container_qty = None

                if sel_c:
                    c_id = c_opts[sel_c]
                    drivers = transport_service.get_drivers_by_contractor(c_id)
                    d_opts = {d.name: d.id for d in drivers}
                    sel_d = st.selectbox(f"Chofer #{load.id}", list(d_opts.keys()), key=f"d_{load.id}")
                    
                    # Logic: Truck Type Selection
                    # If Origin is Treatment Plant, force AMPLIROLL
                    is_treatment_origin = load.origin_treatment_plant_id is not None
                    allowed_truck_types = ["BATEA", "AMPLIROLL"]
                    # Si la solicitud es de una planta de cliente (facility), filtrar tipos permitidos
                    if load.origin_facility_id:
                        fac = location_service.get_facility_by_id(load.origin_facility_id)
                        if fac and fac.allowed_vehicle_types:
                            allowed_truck_types = [t for t in fac.allowed_vehicle_types.split(',') if t in ["BATEA", "AMPLIROLL"]]
                    if is_treatment_origin:
                        # Force Ampliroll
                        sel_truck_type = "AMPLIROLL"
                        st.info("Origen Planta Tratamiento -> Requiere Camión AMPLIROLL")
                    else:
                        sel_truck_type = st.selectbox(f"Tipo de Camión #{load.id}", allowed_truck_types, key=f"tt_{load.id}")

                    # Filter vehicles by type
                    all_vehicles = transport_service.get_vehicles_by_contractor(c_id)
                    # Handle case where vehicle might not have type set (legacy data) - default to BATEA or show all?
                    # Better to filter strictly if type is present.
                    filtered_vehicles = [v for v in all_vehicles if getattr(v, 'type', 'BATEA') == sel_truck_type]
                    
                    if not filtered_vehicles:
                        st.warning(f"No hay camiones tipo {sel_truck_type} para este transportista.")
                        v_opts = {}
                        sel_v = None
                    else:
                        v_opts = {f"{v.license_plate} ({v.max_capacity}t)": v.id for v in filtered_vehicles}
                        sel_v = st.selectbox(f"Camión #{load.id}", list(v_opts.keys()), key=f"v_{load.id}")
                    
                    # If Ampliroll, ask for Container Count
                    if sel_truck_type == "AMPLIROLL":
                        container_qty = st.number_input(f"Cantidad Contenedores #{load.id}", min_value=1, value=1, step=1, key=f"cont_{load.id}")

            with col2:
                st.markdown("#### Destino y Fecha")
                
                # Logic: If Origin is Treatment Plant, Destination MUST be Site
                is_treatment_origin = load.origin_treatment_plant_id is not None
                
                if is_treatment_origin:
                    st.info("Origen: Planta Tratamiento -> Destino: Predio")
                    dest_type = "Predio (Disposición)"
                else:
                    dest_type = st.radio("Tipo Destino", ["Predio (Disposición)", "Planta Tratamiento"], key=f"dtype_{load.id}", horizontal=True)
                
                sel_site_id = None
                sel_plant_id = None
                
                if dest_type == "Predio (Disposición)":
                    sites = location_service.get_all_sites()
                    s_opts = {s.name: s.id for s in sites}
                    sel_s = st.selectbox(f"Predio Destino #{load.id}", list(s_opts.keys()), key=f"s_{load.id}")
                    if sel_s: sel_site_id = s_opts[sel_s]
                else:
                    plants = treatment_plant_service.get_all_plants()
                    p_opts = {p.name: p.id for p in plants}
                    sel_p = st.selectbox(f"Planta Tratamiento #{load.id}", list(p_opts.keys()), key=f"p_{load.id}")
                    if sel_p: sel_plant_id = p_opts[sel_p]
                
                # Date Planning
                # Handle both datetime and date objects safely
                if isinstance(load.requested_date, datetime.datetime):
                    default_date = load.requested_date.date()
                elif isinstance(load.requested_date, datetime.date):
                    default_date = load.requested_date
                else:
                    default_date = datetime.date.today()

                plan_date = st.date_input(f"Fecha Programada #{load.id}", value=default_date, key=f"pd_{load.id}")
                plan_time = st.time_input(f"Hora Programada #{load.id}", value=datetime.time(8, 0), key=f"pt_{load.id}")

            with col3:
                st.markdown("#### Acción")
                st.write("") # Spacer
                st.write("")
                if st.button(f"Asignar y Programar", key=f"btn_{load.id}"):
                    if sel_d and sel_v and (sel_site_id or sel_plant_id):
                        try:
                            # Combine Date and Time
                            scheduled_dt = datetime.datetime.combine(plan_date, plan_time)
                            
                            ops_service.assign_resources(
                                load_id=load.id,
                                driver_id=d_opts[sel_d],
                                vehicle_id=v_opts[sel_v],
                                scheduled_date=scheduled_dt,
                                site_id=sel_site_id,
                                treatment_plant_id=sel_plant_id,
                                container_quantity=container_qty
                            )
                            st.success(f"Solicitud #{load.id} programada exitosamente para {scheduled_dt}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Complete todos los campos.")

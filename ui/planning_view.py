import streamlit as st
from database.db_manager import DatabaseManager
from services.operations_service import OperationsService
from services.masters.transport_service import TransportService
from services.masters.location_service import LocationService
from services.masters.disposal_service import DisposalService
from services.masters.treatment_service import TreatmentService
import datetime

def planning_page():
    st.title("🗓️ Planificación de Retiros")
    
    db = DatabaseManager()
    ops_service = OperationsService(db)
    transport_service = TransportService(db)
    location_service = LocationService(db)
    disposal_service = DisposalService(db)
    treatment_service = TreatmentService(db)
    
    # 1. Fetch Requested Loads
    requested_loads = ops_service.get_loads_by_status('Requested')
    
    if not requested_loads:
        st.info("No hay solicitudes pendientes de planificación.")
        return
        
    st.write(f"Pendientes: {len(requested_loads)}")
    
    # 2. Planning Interface
    for load in requested_loads:
        req_date_str = load.requested_date if load.requested_date else "Sin fecha"
        with st.expander(f"Solicitud #{load.id} - Planta ID: {load.origin_facility_id} - Para: {req_date_str}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Transporte")
                contractors = transport_service.get_all_contractors()
                c_opts = {c.name: c.id for c in contractors}
                sel_c = st.selectbox(f"Transportista #{load.id}", list(c_opts.keys()), key=f"c_{load.id}")
                
                if sel_c:
                    c_id = c_opts[sel_c]
                    drivers = transport_service.get_drivers_by_contractor(c_id)
                    d_opts = {d.name: d.id for d in drivers}
                    sel_d = st.selectbox(f"Chofer #{load.id}", list(d_opts.keys()), key=f"d_{load.id}")
                    
                    vehicles = transport_service.get_vehicles_by_contractor(c_id)
                    v_opts = {f"{v.license_plate} ({v.max_capacity}t)": v.id for v in vehicles}
                    sel_v = st.selectbox(f"Camión #{load.id}", list(v_opts.keys()), key=f"v_{load.id}")

            with col2:
                st.markdown("#### Destino y Fecha")
                sites = location_service.get_all_sites()
                s_opts = {s.name: s.id for s in sites}
                sel_s = st.selectbox(f"Predio Destino #{load.id}", list(s_opts.keys()), key=f"s_{load.id}")
                
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
                    if sel_d and sel_v and sel_s:
                        try:
                            # Combine Date and Time
                            scheduled_dt = datetime.datetime.combine(plan_date, plan_time)
                            
                            ops_service.assign_resources(
                                load_id=load.id,
                                driver_id=d_opts[sel_d],
                                vehicle_id=v_opts[sel_v],
                                site_id=s_opts[sel_s],
                                scheduled_date=scheduled_dt
                            )
                            st.success(f"Solicitud #{load.id} programada exitosamente para {scheduled_dt}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Complete todos los campos.")

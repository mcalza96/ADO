import streamlit as st
from services.operations_service import OperationsService
from services.masters.transport_service import TransportService
from services.masters.treatment_service import TreatmentService
from services.masters.disposal_service import DisposalService
from services.masters.client_service import ClientService
from database.db_manager import DatabaseManager
from models.operations.load import Load
import datetime

def operations_page():
    st.header("Operaciones Centrales (El Viaje)")
    
    db = DatabaseManager()
    ops_service = OperationsService(db)
    transport_service = TransportService(db)
    treatment_service = TreatmentService(db)
    disposal_service = DisposalService(db)
    client_service = ClientService(db)
    
    tab_schedule, tab_dispatch, tab_reception, tab_list = st.tabs(["Programar Viaje", "Despacho (Salida)", "Recepción (Llegada)", "Historial"])
    
    # --- Tab 1: Schedule Load ---
    with tab_schedule:
        st.subheader("Programar Nuevo Viaje")
        
        # Load necessary data for dropdowns
        clients = client_service.get_all_clients()
        contractors = transport_service.get_all_contractors()
        sites = disposal_service.get_all_sites()
        
        if not clients or not contractors or not sites:
            st.warning("Faltan datos maestros (Clientes, Transportistas o Predios).")
        else:
            with st.form("schedule_load_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Origin Selection
                    client_opts = {c.name: c.id for c in clients}
                    sel_client = st.selectbox("Cliente (Generador)", list(client_opts.keys()))
                    facilities = treatment_service.get_facilities_by_client(client_opts[sel_client])
                    
                    fac_opts = {f.name: f.id for f in facilities} if facilities else {}
                    sel_facility = st.selectbox("Planta Origen", list(fac_opts.keys())) if facilities else None
                    
                    # Batch Selection (Optional at scheduling?)
                    batches = treatment_service.get_batches_by_facility(fac_opts[sel_facility]) if sel_facility else []
                    batch_opts = {b.batch_code: b.id for b in batches}
                    sel_batch = st.selectbox("Lote (Batch)", list(batch_opts.keys())) if batches else None

                with col2:
                    # Transport Selection
                    cont_opts = {c.name: c.id for c in contractors}
                    sel_contractor = st.selectbox("Transportista", list(cont_opts.keys()))
                    
                    drivers = transport_service.get_drivers_by_contractor(cont_opts[sel_contractor])
                    driver_opts = {d.name: d.id for d in drivers} if drivers else {}
                    sel_driver = st.selectbox("Chofer", list(driver_opts.keys())) if drivers else None
                    
                    vehicles = transport_service.get_vehicles_by_contractor(cont_opts[sel_contractor])
                    vehicle_opts = {v.license_plate: v.id for v in vehicles} if vehicles else {}
                    sel_vehicle = st.selectbox("Camión", list(vehicle_opts.keys())) if vehicles else None

                # Destination
                site_opts = {s.name: s.id for s in sites}
                sel_site = st.selectbox("Predio Destino", list(site_opts.keys()))
                
                sched_date = st.date_input("Fecha Programada", datetime.date.today())
                
                if st.form_submit_button("Programar Viaje"):
                    if sel_facility and sel_driver and sel_vehicle and sel_site:
                        try:
                            # Get IDs
                            f_id = fac_opts[sel_facility]
                            d_id = driver_opts[sel_driver]
                            v_id = vehicle_opts[sel_vehicle]
                            s_id = site_opts[sel_site]
                            b_id = batch_opts[sel_batch] if sel_batch else None
                            
                            # Create Load
                            load = Load(
                                id=None, driver_id=d_id, vehicle_id=v_id, origin_facility_id=f_id,
                                destination_site_id=s_id, batch_id=b_id, status='Scheduled',
                                scheduled_date=sched_date, created_by_user_id=st.session_state['user'].id
                            )
                            ops_service.create_load(load)
                            st.success("Viaje programado exitosamente")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Faltan datos requeridos")

    # --- Tab 2: Dispatch ---
    with tab_dispatch:
        st.subheader("Registrar Salida (Despacho)")
        loads = ops_service.get_all_loads()
        scheduled_loads = [l for l in loads if l.status == 'Scheduled']
        
        if not scheduled_loads:
            st.info("No hay viajes programados pendientes de despacho.")
        else:
            # Simple selection by ID for MVP
            l_opts = {f"ID {l.id} - {l.scheduled_date}": l.id for l in scheduled_loads}
            sel_load_key = st.selectbox("Seleccionar Viaje", list(l_opts.keys()))
            sel_load_id = l_opts[sel_load_key]
            
            with st.form("dispatch_form"):
                ticket = st.text_input("Nro Guía / Ticket")
                gross = st.number_input("Peso Bruto (kg)", min_value=0.0)
                tare = st.number_input("Tara (kg)", min_value=0.0)
                dispatch_time = st.time_input("Hora Salida", datetime.datetime.now().time())
                
                if st.form_submit_button("Registrar Salida"):
                    try:
                        # Update load
                        ops_service.update_load_status(
                            sel_load_id, 
                            status='InTransit',
                            ticket_number=ticket,
                            weight_gross=gross,
                            weight_tare=tare,
                            weight_net=gross-tare,
                            dispatch_time=datetime.datetime.combine(datetime.date.today(), dispatch_time)
                        )
                        st.success("Despacho registrado. Viaje en tránsito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- Tab 3: Reception ---
    with tab_reception:
        st.subheader("Registrar Llegada (Recepción)")
        transit_loads = [l for l in loads if l.status == 'InTransit']
        
        if not transit_loads:
            st.info("No hay viajes en tránsito.")
        else:
            tl_opts = {f"ID {l.id} - Ticket {l.ticket_number}": l.id for l in transit_loads}
            sel_transit_key = st.selectbox("Seleccionar Viaje en Tránsito", list(tl_opts.keys()))
            sel_transit_id = tl_opts[sel_transit_key]
            
            with st.form("reception_form"):
                arrival_time = st.time_input("Hora Llegada", datetime.datetime.now().time())
                confirm = st.checkbox("Confirmar Recepción Conforme")
                
                if st.form_submit_button("Cerrar Viaje"):
                    if confirm:
                        try:
                            ops_service.update_load_status(
                                sel_transit_id,
                                status='Delivered',
                                arrival_time=datetime.datetime.combine(datetime.date.today(), arrival_time)
                            )
                            st.success("Viaje finalizado exitosamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Debe confirmar la recepción.")

    # --- Tab 4: History ---
    with tab_list:
        st.subheader("Historial de Viajes")
        if loads:
            # Flatten data for display could be better but raw dict is fine for MVP
            st.dataframe([vars(l) for l in loads], use_container_width=True)
        else:
            st.info("No hay viajes registrados.")

import streamlit as st
from container import get_container
import datetime

def requests_page(treatment_plant_service=None):
    st.title("📝 Solicitud de Retiros")
    st.markdown("Ingrese las solicitudes de retiro para sus plantas.")
    
    services = get_container()
    client_service = services.client_service
    location_service = services.location_service
    ops_service = services.logistics_service
    treatment_plant_service = treatment_plant_service or services.treatment_plant_service
    
    # 1. Select Client (Simulating User Context)
    clients = client_service.get_all_clients()
    if not clients:
        st.error("No hay clientes configurados.")
        return
        
    c_opts = {c.name: c.id for c in clients}
    sel_client = st.selectbox("Cliente (Generador)", list(c_opts.keys()))
    client_id = c_opts[sel_client]
    
    # 2. Select Facility
    facilities = treatment_plant_service.get_by_client(client_id)
    if not facilities:
        st.warning("Este cliente no tiene plantas registradas.")
        return
        
    f_opts = {f.name: f.id for f in facilities}
    sel_facility = st.selectbox("Planta de Origen", list(f_opts.keys()))
    facility_id = f_opts[sel_facility]
    
    # 3. Request Form
    with st.form("request_form"):
        st.write("Detalles de la Solicitud")
        req_date = st.date_input("Fecha Solicitada de Retiro", datetime.date.today())
        num_requests = st.number_input("Cantidad de Camiones Solicitados", min_value=1, max_value=20, value=1)
        
        if st.form_submit_button("🚀 Enviar Solicitud"):
            try:
                for _ in range(num_requests):
                    ops_service.create_request(facility_id, req_date)
                st.success(f"✅ Se han generado {num_requests} solicitudes de retiro para el {req_date} exitosamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al crear solicitud: {e}")

    st.divider()
    st.subheader("🔍 Seguimiento de Solicitudes")
    
    # Fetch loads for this facility
    loads = ops_service.get_loads_by_facility(facility_id)
    
    if not loads:
        st.info("No hay solicitudes registradas para esta planta.")
    else:
        # Simple table view
        data = []
        for l in loads:
            data.append({
                "ID": l.id,
                "Fecha Programada": l.scheduled_date,
                "Estado": l.status,
                "Transportista": l.contractor_id if l.contractor_id else "Pendiente",
                "Destino": "Asignado" if (l.destination_site_id or l.destination_treatment_plant_id) else "Pendiente"
            })
        
        st.dataframe(data, use_container_width=True)
                
    # 4. View Active Requests
    st.divider()
    st.subheader("Solicitudes Pendientes")
    pending_loads = ops_service.get_loads_by_status('Requested')
    # Filter by selected facility for cleaner view
    my_loads = [l for l in pending_loads if l.origin_facility_id == facility_id]
    
    if my_loads:
        st.info(f"Hay {len(my_loads)} solicitudes pendientes para esta planta.")
        # Simple list view
        for load in my_loads:
            req_date_str = load.requested_date if load.requested_date else "Sin fecha"
            st.text(f"ID: {load.id} | Solicitado para: {req_date_str} | Estado: {load.status}")
    else:
        st.write("No hay solicitudes pendientes.")

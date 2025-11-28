import streamlit as st
from services.masters.client_service import ClientService
from database.db_manager import DatabaseManager
from models.masters.client import Client

def clients_page():
    st.header("Gestión de Clientes (Generadores)")
    
    db = DatabaseManager()
    client_service = ClientService(db)
    
    # Form to add new client
    with st.expander("Agregar Nuevo Cliente"):
        with st.form("add_client_form"):
            name = st.text_input("Nombre Empresa")
            rut = st.text_input("RUT")
            col1, col2 = st.columns(2)
            with col1:
                contact_name = st.text_input("Nombre Contacto")
            with col2:
                contact_email = st.text_input("Email Contacto")
            address = st.text_input("Dirección")
            
            submitted = st.form_submit_button("Guardar Cliente")
            if submitted:
                if name:
                    new_client = Client(
                        id=None,
                        name=name,
                        rut=rut,
                        contact_name=contact_name,
                        contact_email=contact_email,
                        address=address
                    )
                    try:
                        client_service.create_client(new_client)
                        st.success("Cliente creado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear cliente: {e}")
                else:
                    st.warning("El nombre es obligatorio")

    # List existing clients
    st.subheader("Listado de Clientes")
    clients = client_service.get_all_clients()
    
    if clients:
        # Prepare data for dataframe
        data = []
        for c in clients:
            data.append({
                "ID": c.id,
                "Nombre": c.name,
                "RUT": c.rut,
                "Contacto": c.contact_name,
                "Email": c.contact_email,
                "Dirección": c.address
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No hay clientes registrados aún.")

    # --- Facilities Management ---
    st.markdown("---")
    from services.masters.location_service import LocationService
    loc_service = LocationService(db)
    st.subheader("Parametrización de Plantas de Cliente (Facilities)")
    
    # Reuse clients list
    for client in clients:
        st.markdown(f"**{client.name}**")
        facilities = loc_service.get_facilities_by_client(client.id)
        if not facilities:
            st.info("Sin plantas registradas para este cliente.")
            continue
        for fac in facilities:
            colf1, colf2 = st.columns([2,2])
            with colf1:
                st.write(f"Planta: {fac.name}")
                st.write(f"Dirección: {fac.address or '-'}")
            with colf2:
                allowed_types = fac.allowed_vehicle_types.split(',') if fac.allowed_vehicle_types else ["BATEA", "AMPLIROLL"]
                new_types = st.multiselect(
                    f"Tipos de camión permitidos para {fac.name}",
                    ["BATEA", "AMPLIROLL"],
                    default=allowed_types,
                    key=f"allowed_types_{fac.id}"
                )
                if st.button(f"Guardar tipos para {fac.name}", key=f"save_types_{fac.id}"):
                    loc_service.update_facility_allowed_vehicle_types(fac.id, ','.join(new_types))
                    st.success("Actualizado")
                    st.rerun()


import streamlit as st
from container import get_container
from models.masters.client import Client
from models.masters.treatment_plant import TreatmentPlant


def clients_page(treatment_plant_service=None):
    st.header("Gestión de Clientes (Generadores)")
    
    services = get_container()
    client_service = services.client_service
    location_service = services.location_service
    treatment_plant_service = treatment_plant_service or services.treatment_plant_service
    
    # Form to add new client
    with st.expander("➕ Agregar Nuevo Cliente"):
        with st.form("add_client_form"):
            name = st.text_input("Nombre Empresa *")
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
                        st.success("✅ Cliente creado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al crear cliente: {e}")
                else:
                    st.warning("⚠️ El nombre es obligatorio")

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
    st.subheader("Gestión de Plantas de Tratamiento")
    
    if not clients:
        st.info("Primero cree un cliente para asociar plantas.")
    else:
        # Select client to create facility for
        client_opts = {f"{c.name} (ID: {c.id})": c.id for c in clients}
        selected_client_display = st.selectbox("Seleccionar Cliente", list(client_opts.keys()), key="facility_client_select")
        selected_client_id = client_opts[selected_client_display]
        
        # Form to create a new facility
        with st.expander("➕ Nueva Planta de Tratamiento"):
            with st.form("add_facility_form"):
                fac_name = st.text_input("Nombre de la Planta *")
                fac_address = st.text_input("Dirección")
                col1, col2 = st.columns(2)
                with col1:
                    fac_lat = st.number_input("Latitud", format="%.6f", value=-33.4489)
                with col2:
                    fac_lon = st.number_input("Longitud", format="%.6f", value=-70.6693)
                
                allowed_types = st.multiselect(
                    "Tipos de Camión Permitidos",
                    ["BATEA", "AMPLIROLL"],
                    default=["BATEA", "AMPLIROLL"]
                )
                
                fac_submitted = st.form_submit_button("Crear Planta")
                if fac_submitted:
                    if fac_name:
                        try:
                            treatment_plant_service.create_plant(
                                name=fac_name,
                                address=fac_address,
                                client_id=selected_client_id,
                                latitude=fac_lat,
                                longitude=fac_lon,
                                allowed_vehicle_types=",".join(allowed_types) if allowed_types else None
                            )
                            st.success("✅ Planta creada exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear planta: {e}")
                    else:
                        st.warning("⚠️ El nombre de la planta es obligatorio")
        
        # Display facilities for selected client
        st.markdown(f"**Plantas del Cliente Seleccionado:**")
        facilities = treatment_plant_service.get_by_client(selected_client_id)
        if facilities:
            for fac in facilities:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"🏭 **{fac.name}**")
                        st.caption(f"Dirección: {fac.address or '-'}")
                    with col2:
                        current_types = fac.allowed_vehicle_types.split(',') if fac.allowed_vehicle_types else ["BATEA", "AMPLIROLL"]
                        st.write(f"Tipos permitidos: {', '.join(current_types)}")
                    with col3:
                        st.caption(f"ID: {fac.id}")
                    st.divider()
        else:
            st.info("Este cliente no tiene plantas registradas.")


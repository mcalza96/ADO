
import streamlit as st
from container import get_container

def treatment_plants_page():
    st.subheader("🏭 Plantas de Tratamiento (Propias)")
    
    services = get_container()
    service = services.treatment_plant_service
    
    # Create Form
    with st.expander("Nueva Planta de Tratamiento"):
        with st.form("new_plant_form"):
            name = st.text_input("Nombre de Planta")
            address = st.text_input("Dirección")
            resolution = st.text_input("Resolución Sanitaria (RCA)")
            
            if st.form_submit_button("Crear Planta"):
                if name:
                    service.create_plant(name, address, resolution)
                    st.success("Planta creada exitosamente.")
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio.")
    
    # List
    plants = service.get_all_plants()
    if plants:
        st.dataframe([
            {"ID": p.id, "Nombre": p.name, "Dirección": p.address, "RCA": p.authorization_resolution}
            for p in plants
        ])
    else:
        st.info("No hay plantas registradas.")

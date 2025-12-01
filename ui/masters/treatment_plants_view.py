
import streamlit as st
from container import get_container

def treatment_plants_page(treatment_plant_service=None):
    st.subheader("🏭 Plantas de Tratamiento (Propias)")
    
    services = get_container()
    service = treatment_plant_service or services.treatment_plant_service
    
    # Create Form
    with st.expander("Nueva Planta de Tratamiento"):
        with st.form("new_plant_form"):
            name = st.text_input("Nombre de Planta")
            address = st.text_input("Dirección")
            
            if st.form_submit_button("Crear Planta"):
                if name:
                    service.create_plant(name, address)
                    st.success("Planta creada exitosamente.")
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio.")
    
    # List
    plants = service.get_all()
    if plants:
        st.dataframe([
            {"ID": p.id, "Nombre": p.name, "Dirección": p.address}
            for p in plants
        ])
    else:
        st.info("No hay plantas registradas.")

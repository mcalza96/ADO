import streamlit as st
from database.db_manager import DatabaseManager
from services.masters.container_service import ContainerService
from services.masters.treatment_plant_service import TreatmentPlantService

def containers_view():
    st.title("📦 Gestión de Contenedores")
    
    db = DatabaseManager()
    service = ContainerService(db)
    plant_service = TreatmentPlantService(db)
    
    # Create New Container
    with st.expander("➕ Nuevo Contenedor", expanded=False):
        with st.form("new_container"):
            code = st.text_input("Código del Contenedor (ej. CONT-001)")
            
            plants = plant_service.get_all_plants()
            plant_opts = {p.name: p.id for p in plants}
            plant_opts["Sin Asignar"] = None
            
            sel_plant = st.selectbox("Ubicación Inicial", list(plant_opts.keys()))
            
            if st.form_submit_button("Crear Contenedor"):
                try:
                    service.create_container(code, plant_opts[sel_plant])
                    st.success(f"Contenedor {code} creado exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.divider()
    
    # List Containers
    containers = service.get_all_containers()
    if not containers:
        st.info("No hay contenedores registrados.")
        return
        
    data = []
    for c in containers:
        # Find plant name if assigned
        plant_name = "N/A"
        if c.current_plant_id:
            # Inefficient but fine for MVP
            p = next((p for p in plants if p.id == c.current_plant_id), None)
            if p: plant_name = p.name
            
        data.append({
            "ID": c.id,
            "Código": c.code,
            "Estado": c.status,
            "Ubicación Actual": plant_name
        })
        
    st.dataframe(data, use_container_width=True)

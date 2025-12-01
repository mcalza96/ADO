import streamlit as st
from ui.masters.clients_view import clients_page
from ui.masters.transport_view import transport_page
from ui.masters.treatment_view import treatment_page
from ui.masters.disposal_view import disposal_page
from ui.masters.treatment_plants_view import treatment_plants_page

def config_page(treatment_plant_service=None):
    st.title("⚙️ Configuración del Sistema")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Clientes (Generadores)", 
        "🚛 Transportistas", 
        "🏭 Plantas (Origen)", 
        "🌾 Predios (Destino)",
        "🧪 Plantas Tratamiento (Propias)"
    ])
    
    with tab1:
        clients_page(treatment_plant_service=treatment_plant_service)
        
    with tab2:
        transport_page()
        
    with tab3:
        treatment_page(treatment_plant_service=treatment_plant_service)
        
    with tab4:
        disposal_page()
        
    with tab5:
        treatment_plants_page(treatment_plant_service=treatment_plant_service)

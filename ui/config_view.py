import streamlit as st
from ui.masters.clients_view import clients_page
from ui.masters.transport_view import transport_page
from ui.masters.treatment_view import treatment_page
from ui.masters.disposal_view import disposal_page

def config_page():
    st.title("⚙️ Configuración del Sistema")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Clientes (Generadores)", 
        "🚛 Transportistas", 
        "🏭 Plantas (Origen)", 
        "🌾 Predios (Destino)"
    ])
    
    with tab1:
        clients_page()
        
    with tab2:
        transport_page()
        
    with tab3:
        treatment_page()
        
    with tab4:
        disposal_page()

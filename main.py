import streamlit as st
from ui.auth.login import login_page
from ui.masters.clients_view import clients_page
from ui.masters.transport_view import transport_page
from ui.masters.treatment_view import treatment_page
from ui.masters.disposal_view import disposal_page
from ui.operations.operations_view import operations_page
from ui.operations.dashboard_view import dashboard_page

# Page configuration
st.set_page_config(
    page_title="Biosolids ERP",
    page_icon="🚛",
    layout="wide"
)

def main():
    # Initialize session state for user
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Check if user is logged in
    if st.session_state['user'] is None:
        login_page()
    else:
        # Main App Layout
        user = st.session_state['user']
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("Biosolids ERP")
            st.write(f"User: **{user.username}** ({user.role})")
            st.divider()
            
            menu = st.radio(
                "Navegación",
                ["Dashboard", "Clientes", "Transportistas", "Plantas", "Predios", "Operaciones", "Configuración"]
            )
            
            st.divider()
            if st.button("Logout"):
                st.session_state['user'] = None
                st.rerun()

        # Main Content Area
        if menu == "Dashboard":
            dashboard_page()
                
        elif menu == "Clientes":
            clients_page()
        elif menu == "Transportistas":
            transport_page()
        elif menu == "Plantas":
            treatment_page()
        elif menu == "Predios":
            disposal_page()
        elif menu == "Operaciones":
            operations_page()
        elif menu == "Configuración":
            st.warning("Configuración del sistema")

if __name__ == "__main__":
    main()

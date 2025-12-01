import streamlit as st
from ui.masters import containers_view, transport_view, locations_view
from ui.masters.clients_view import clients_page
from ui.masters.treatment_plants_view import treatment_plants_page


def config_page(
    client_service,
    contractor_service,
    treatment_plant_service,
    container_service,
    location_service,
    transport_service,
    auth_service
):
    """
    Orquestador de vistas de configuración de maestros.
    Recibe todos los servicios necesarios y los distribuye a las sub-vistas.
    
    Args:
        client_service: ClientService instance
        contractor_service: ContractorService instance
        treatment_plant_service: TreatmentPlantService instance
        container_service: ContainerService instance
        location_service: LocationService instance
        transport_service: TransportService instance
        auth_service: AuthService instance
    """
    st.title("⚙️ Configuración del Sistema")
    
    # Main configuration tabs
    tab_empresas, tab_transporte, tab_agronomia, tab_seguridad = st.tabs([
        "🏢 Empresas",
        "🚛 Transporte",
        "🌾 Agronomía",
        "🔐 Seguridad"
    ])
    
    # ==========================================
    # TAB 1: EMPRESAS (Clients & Treatment Plants)
    # ==========================================
    with tab_empresas:
        st.header("Gestión de Empresas")
        
        sub_tab_clients, sub_tab_plants = st.tabs([
            "Clientes (Generadores)",
            "Plantas de Tratamiento (Propias)"
        ])
        
        with sub_tab_clients:
            # Call existing clients_page - need to refactor later to use render pattern
            # For now, passing treatment_plant_service for backward compatibility
            clients_page(treatment_plant_service=treatment_plant_service)
        
        with sub_tab_plants:
            # Call existing treatment_plants_page
            treatment_plants_page(treatment_plant_service=treatment_plant_service)
    
    # ==========================================
    # TAB 2: TRANSPORTE
    # ==========================================
    with tab_transporte:
        st.header("Gestión de Transporte y Logística")
        
        # Horizontal radio for transport sub-sections
        transport_section = st.radio(
            "Seleccione:",
            ["Contratistas", "Vehículos", "Conductores", "Contenedores"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if transport_section in ["Contratistas", "Vehículos", "Conductores"]:
            # Use refactored transport_view with dependency injection
            transport_view.render(transport_service, contractor_service)
        
        elif transport_section == "Contenedores":
            # Use refactored containers_view with dependency injection
            containers_view.render(container_service, contractor_service)
    
    # ==========================================
    # TAB 3: AGRONOMÍA (Sites & Plots)
    # ==========================================
    with tab_agronomia:
        # Use new locations_view with master-detail layout
        locations_view.render(location_service)
    
    # ==========================================
    # TAB 4: SEGURIDAD (Users & Permissions)
    # ==========================================
    with tab_seguridad:
        st.header("Gestión de Usuarios y Seguridad")
        st.info("🚧 Módulo de gestión de usuarios en desarrollo")
        
        # Placeholder for future user management view
        # user_management_view.render(auth_service)
        
        # For now, show basic user info
        if 'user' in st.session_state and st.session_state['user']:
            user = st.session_state['user']
            st.write(f"**Usuario actual:** {user.username}")
            st.write(f"**Rol:** {user.role}")
            st.write(f"**Nombre completo:** {user.full_name}")
        
        st.divider()
        st.caption("💡 Próximamente: Gestión de usuarios, roles y permisos")

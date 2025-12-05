import streamlit as st
from ui.masters import containers_view, transport_view, locations_view, security_view
from ui.generic_master_view import GenericMasterView, FieldConfig
from domain.shared.entities.client import Client
from domain.processing.entities.treatment_plant import TreatmentPlant
from domain.processing.entities.facility import Facility
from domain.logistics.entities.vehicle import VehicleType


def config_page(container):
    """
    Orquestador de vistas de configuración de maestros.
    Recibe el container de servicios y los distribuye a las sub-vistas.
    
    Args:
        container: SimpleNamespace con todos los servicios inyectados
    """
    # Extract services from container
    client_service = container.client_service
    facility_service = container.facility_service
    contractor_service = container.contractor_service
    treatment_plant_service = container.treatment_plant_service
    container_service = container.container_service
    location_service = container.location_service
    driver_service = container.driver_service
    vehicle_service = container.vehicle_service
    auth_service = container.auth_service
    
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
        
        sub_tab_clients, sub_tab_facilities, sub_tab_plants = st.tabs([
            "Clientes (Generadores)",
            "Plantas del Cliente (Orígenes)",
            "Plantas de Tratamiento (Propias)"
        ])
        
        with sub_tab_clients:
            # Use GenericMasterView for Clients
            GenericMasterView(
                service=client_service,
                model_class=Client,
                title="Clientes (Generadores)",
                display_columns=["name", "rut", "contact_name", "contact_email"],
                form_config={
                    "name": FieldConfig(label="Nombre Empresa", required=True),
                    "rut": FieldConfig(label="RUT"),
                    "contact_name": FieldConfig(label="Nombre Contacto"),
                    "contact_email": FieldConfig(label="Email Contacto"),
                    "address": FieldConfig(label="Dirección", widget="text_area")
                }
            ).render()
        
        with sub_tab_facilities:
            # Use GenericMasterView for Client Facilities (origin plants)
            GenericMasterView(
                service=facility_service,
                model_class=Facility,
                title="Plantas del Cliente (Instalaciones de Origen)",
                display_columns=["name", "client_id", "address", "allowed_vehicle_types"],
                form_config={
                    "name": FieldConfig(label="Nombre de Planta", required=True),
                    "client_id": FieldConfig(
                        label="Cliente",
                        widget="selectbox",
                        options=client_service,
                        required=True,
                        help="Seleccione el cliente dueño de esta instalación"
                    ),
                    "address": FieldConfig(label="Dirección", widget="text_area"),
                    "latitude": FieldConfig(label="Latitud", widget="number_input"),
                    "longitude": FieldConfig(label="Longitud", widget="number_input"),
                    "allowed_vehicle_types": FieldConfig(
                        label="Tipos de Vehículos Permitidos",
                        widget="multiselect",
                        options=VehicleType.choices(),
                        help="Seleccione los tipos de vehículos que pueden operar en esta planta"
                    )
                }
            ).render()
        
        with sub_tab_plants:
            # Use GenericMasterView for Treatment Plants (own processing plants)
            GenericMasterView(
                service=treatment_plant_service,
                model_class=TreatmentPlant,
                title="Plantas de Tratamiento (Propias)",
                display_columns=["name", "address", "authorization_resolution", "state_permit_number"],
                form_config={
                    "name": FieldConfig(label="Nombre de Planta", required=True),
                    "address": FieldConfig(label="Dirección", widget="text_area"),
                    "latitude": FieldConfig(label="Latitud", widget="number_input"),
                    "longitude": FieldConfig(label="Longitud", widget="number_input"),
                    "authorization_resolution": FieldConfig(
                        label="Resolución de Autorización",
                        help="Número de resolución sanitaria de autorización"
                    ),
                    "state_permit_number": FieldConfig(
                        label="Nº Permiso Estatal",
                        help="Número de permiso otorgado por el estado"
                    ),
                    "allowed_vehicle_types": FieldConfig(
                        label="Tipos de Vehículos Permitidos",
                        widget="multiselect",
                        options=VehicleType.choices(),
                        help="Seleccione los tipos de vehículos que pueden operar"
                    )
                }
            ).render()
    
    # ==========================================
    # TAB 2: TRANSPORTE
    # ==========================================
    with tab_transporte:
        # Use refactored transport_view with dependency injection
        transport_view.render(driver_service, vehicle_service, contractor_service, container_service)
    
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
        # Usar security_view extraído para mejor SRP
        current_user = st.session_state.get('user')
        security_view.render(auth_service, current_user)

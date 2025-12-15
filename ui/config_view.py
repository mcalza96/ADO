import streamlit as st
from ui.masters import containers_view, transport_view, locations_view, security_view
from ui.generic_master_view import GenericMasterView, FieldConfig
from ui.helpers.facility_view_helper import _render_facilities_view
from domain.shared.entities.client import Client
from domain.processing.entities.treatment_plant import TreatmentPlant
from domain.processing.entities.facility import Facility
from domain.logistics.entities.vehicle import VehicleType
from domain.logistics.entities.contractor import Contractor, ContractorType
from domain.logistics.entities.driver import Driver
from domain.logistics.entities.vehicle import Vehicle
from enum import Enum


# Tipos de equipos de disposición
class DisposalEquipmentType(str, Enum):
    """Tipos de equipos para operaciones de disposición."""
    TRACTOR = "TRACTOR"
    EXCAVATOR = "EXCAVATOR"
    LOADER = "LOADER"
    COMPACTOR = "COMPACTOR"
    OTHER = "OTHER"
    
    @classmethod
    def choices(cls) -> list:
        """Retorna lista de tuplas (display_name, value) para selectbox."""
        labels = {
            cls.TRACTOR: "Tractor",
            cls.EXCAVATOR: "Excavadora",
            cls.LOADER: "Cargador Frontal",
            cls.COMPACTOR: "Compactador",
            cls.OTHER: "Otro"
        }
        return [(labels.get(member, member.value), member.value) for member in cls]


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
    
    st.title("Configuración del Sistema")
    
    # Main configuration tabs
    tab_empresas, tab_transporte, tab_disposicion, tab_proveedores, tab_agronomia, tab_seguridad, tab_finanzas = st.tabs([
        "Empresas",
        "Transporte",
        "Disposición",
        "Otros Proveedores",
        "Agronomía",
        "Seguridad",
        "Parámetros Financieros"
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
            # Custom view for Facilities with validation
            _render_facilities_view(facility_service, client_service)
        
        with sub_tab_plants:
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
        transport_view.render(driver_service, vehicle_service, contractor_service, container_service)
    
    # ==========================================
    # TAB 3: DISPOSICIÓN
    # ==========================================
    with tab_disposicion:
        st.header("Gestión de Disposición")
        
        # Función para obtener solo contratistas de disposición
        get_disposal_contractors = lambda: contractor_service.get_contractors_by_type('DISPOSAL')
        
        # Función para obtener solo operadores de contratistas de disposición
        def get_disposal_operators():
            disposal_contractor_ids = {c.id for c in get_disposal_contractors()}
            all_drivers = driver_service.get_all()
            return [d for d in all_drivers if d.contractor_id in disposal_contractor_ids]
        
        sub_tab_contractors, sub_tab_operators, sub_tab_equipment = st.tabs([
            "Contratistas",
            "Operadores",
            "Equipos"
        ])
        
        with sub_tab_contractors:
            st.info("Contratistas que prestan servicios de disposición final de residuos.")
            GenericMasterView(
                service=contractor_service, 
                model_class=Contractor, 
                title="Contratistas de Disposición",
                display_columns=["name", "rut", "contact_name", "phone"],
                data_source=get_disposal_contractors,
                form_config={
                    "name": FieldConfig(label="Nombre Empresa", required=True),
                    "rut": FieldConfig(label="RUT", required=True),
                    "contact_name": FieldConfig(label="Contacto"),
                    "phone": FieldConfig(label="Teléfono"),
                    "contractor_type": FieldConfig(
                        label="Tipo de Proveedor",
                        widget="enum",
                        enum_class=ContractorType,
                        default=ContractorType.DISPOSAL.value,
                        help="Tipo de servicio que presta el contratista"
                    )
                }
            ).render()
        
        with sub_tab_operators:
            st.info("Operadores de maquinaria pesada para disposición.")
            GenericMasterView(
                service=driver_service,
                model_class=Driver,
                title="Operadores de Disposición",
                display_columns=["name", "rut", "license_number", "contractor_id"],
                data_source=get_disposal_operators,
                form_config={
                    "name": FieldConfig(label="Nombre Completo", required=True),
                    "rut": FieldConfig(label="RUT", required=True),
                    "license_number": FieldConfig(
                        label="Nº Licencia/Certificación", 
                        help="Licencia de conducir o certificación de operador"
                    ),
                    "license_type": FieldConfig(
                        label="Tipo de Licencia",
                        help="Ej: Clase D, Operador de Maquinaria Pesada"
                    ),
                    "contractor_id": FieldConfig(
                        label="Contratista",
                        widget="selectbox",
                        options=get_disposal_contractors,
                        required=True,
                        help="Empresa contratista a la que pertenece"
                    )
                }
            ).render()
        
        with sub_tab_equipment:
            st.info("Equipos de disposición: tractores, excavadoras, cargadores, etc.")
            
            # Función para obtener equipos de contratistas de disposición
            def get_disposal_equipment():
                disposal_contractor_ids = {c.id for c in get_disposal_contractors()}
                all_vehicles = vehicle_service.get_all()
                return [v for v in all_vehicles if v.contractor_id in disposal_contractor_ids]
            
            # Filtro por contratista
            disposal_contractors = get_disposal_contractors()
            contractor_options = {"Todos": None}
            contractor_options.update({c.name: c.id for c in disposal_contractors})
            
            selected_contractor_name = st.selectbox(
                "Filtrar por Contratista",
                options=list(contractor_options.keys()),
                key="disposal_equipment_contractor_filter"
            )
            selected_contractor_id = contractor_options[selected_contractor_name]
            
            # Función de filtrado según selección
            def get_filtered_equipment(equipment_type=None):
                disposal_contractor_ids = {c.id for c in disposal_contractors}
                all_vehicles = vehicle_service.get_all()
                filtered = [v for v in all_vehicles if v.contractor_id in disposal_contractor_ids]
                
                # Filtrar por contratista si está seleccionado
                if selected_contractor_id:
                    filtered = [v for v in filtered if v.contractor_id == selected_contractor_id]
                
                # Filtrar por tipo de equipo si se especifica
                if equipment_type:
                    filtered = [v for v in filtered if getattr(v, 'type', None) == equipment_type]
                
                return filtered
            
            equip_tab1, equip_tab2, equip_tab3 = st.tabs(["Tractores", "Excavadoras", "Otros Equipos"])
            
            with equip_tab1:
                GenericMasterView(
                    service=vehicle_service,
                    model_class=Vehicle,
                    title="Tractores",
                    display_columns=["license_plate", "brand", "model", "contractor_id"],
                    data_source=lambda: get_filtered_equipment("TRACTOR"),
                    form_config={
                        "license_plate": FieldConfig(label="Identificador/Patente", required=True),
                        "brand": FieldConfig(label="Marca"),
                        "model": FieldConfig(label="Modelo"),
                        "year": FieldConfig(label="Año", widget="number_input"),
                        "type": FieldConfig(
                            label="Tipo",
                            widget="selectbox",
                            options=DisposalEquipmentType.choices(),
                            default="TRACTOR"
                        ),
                        "tare_weight": FieldConfig(label="Peso (kg)", widget="number_input"),
                        "max_gross_weight": FieldConfig(label="Capacidad (kg)", widget="number_input"),
                        "contractor_id": FieldConfig(
                            label="Contratista",
                            widget="selectbox",
                            options=get_disposal_contractors,
                            required=True
                        )
                    }
                ).render()
            
            with equip_tab2:
                GenericMasterView(
                    service=vehicle_service,
                    model_class=Vehicle,
                    title="Excavadoras",
                    display_columns=["license_plate", "brand", "model", "contractor_id"],
                    data_source=lambda: get_filtered_equipment("EXCAVATOR"),
                    form_config={
                        "license_plate": FieldConfig(label="Identificador/Patente", required=True),
                        "brand": FieldConfig(label="Marca"),
                        "model": FieldConfig(label="Modelo"),
                        "year": FieldConfig(label="Año", widget="number_input"),
                        "type": FieldConfig(
                            label="Tipo",
                            widget="selectbox",
                            options=DisposalEquipmentType.choices(),
                            default="EXCAVATOR"
                        ),
                        "tare_weight": FieldConfig(label="Peso (kg)", widget="number_input"),
                        "max_gross_weight": FieldConfig(label="Capacidad (kg)", widget="number_input"),
                        "contractor_id": FieldConfig(
                            label="Contratista",
                            widget="selectbox",
                            options=get_disposal_contractors,
                            required=True
                        )
                    }
                ).render()
            
            with equip_tab3:
                # Otros equipos: mostrar todos los que NO son TRACTOR ni EXCAVATOR
                def get_other_equipment():
                    all_disposal = get_filtered_equipment()
                    return [v for v in all_disposal if getattr(v, 'type', None) not in ['TRACTOR', 'EXCAVATOR']]
                
                GenericMasterView(
                    service=vehicle_service,
                    model_class=Vehicle,
                    title="Otros Equipos",
                    display_columns=["license_plate", "brand", "model", "type", "contractor_id"],
                    data_source=get_other_equipment,
                    form_config={
                        "license_plate": FieldConfig(label="Identificador/Patente", required=True),
                        "brand": FieldConfig(label="Marca"),
                        "model": FieldConfig(label="Modelo"),
                        "year": FieldConfig(label="Año", widget="number_input"),
                        "type": FieldConfig(
                            label="Tipo",
                            widget="selectbox",
                            options=DisposalEquipmentType.choices(),
                            default="OTHER"
                        ),
                        "tare_weight": FieldConfig(label="Peso (kg)", widget="number_input"),
                        "max_gross_weight": FieldConfig(label="Capacidad (kg)", widget="number_input"),
                        "contractor_id": FieldConfig(
                            label="Contratista",
                            widget="selectbox",
                            options=get_disposal_contractors,
                            required=True
                        )
                    }
                ).render()
    
    # ==========================================
    # TAB 4: OTROS PROVEEDORES
    # ==========================================
    with tab_proveedores:
        st.header("Otros Proveedores")
        st.info("Sección para futuros proveedores: servicios varios, mecánicos, etc.")
        st.caption("Esta sección se habilitará cuando se agreguen nuevos tipos de proveedores al sistema.")
    
    # ==========================================
    # TAB 5: AGRONOMÍA (Sites & Plots)
    # ==========================================
    with tab_agronomia:
        locations_view.render(location_service)
    
    # ==========================================
    # TAB 6: SEGURIDAD (Users & Permissions)
    # ==========================================
    with tab_seguridad:
        current_user = st.session_state.get('user')
        security_view.render(auth_service, current_user)
    
    # ==========================================
    # TAB 7: PARÁMETROS FINANCIEROS
    # ==========================================
    with tab_finanzas:
        from ui.config import financial_parameters_view
        from ui.masters import proforma_master_view
        
        # Sub-tabs for financial configuration
        fin_tab_proformas, fin_tab_config = st.tabs([
            "📋 Maestro de Proformas",
            "⚙️ Configuración Financiera"
        ])
        
        with fin_tab_proformas:
            proforma_master_view.render(proforma_repo=container.proforma_repo)
        
        with fin_tab_config:
            st.info("📌 **Nota:** Los indicadores mensuales (UF, Petróleo) ahora se gestionan en el **Maestro de Proformas**.")
            financial_parameters_view.render(
                economic_repo=container.economic_indicators_repo,
                distance_repo=container.distance_matrix_repo,
                contractor_tariffs_repo=container.contractor_tariffs_repo,
                client_tariffs_repo=container.client_tariffs_repo
            )

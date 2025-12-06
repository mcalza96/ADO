import streamlit as st
from domain.logistics.entities.contractor import Contractor, ContractorType
from domain.logistics.entities.vehicle import Vehicle, VehicleType
from domain.logistics.entities.driver import Driver
from ui.generic_master_view import GenericMasterView, FieldConfig
from ui.masters import containers_view

def render(driver_service, vehicle_service, contractor_service, container_service=None):
    """
    Vista de gestión de Transporte usando Vistas Genéricas.
    
    Args:
        driver_service: Servicio de choferes
        vehicle_service: Servicio de vehículos
        contractor_service: Servicio de contratistas
        container_service: Servicio de contenedores (opcional para compatibilidad)
    """
    st.header("Gestión de Transporte")
    
    # Función para obtener solo contratistas de transporte
    get_transport_contractors = lambda: contractor_service.get_contractors_by_type('TRANSPORT')
    
    # Función para obtener solo choferes de contratistas de transporte
    def get_transport_drivers():
        transport_contractor_ids = {c.id for c in get_transport_contractors()}
        all_drivers = driver_service.get_all()
        return [d for d in all_drivers if d.contractor_id in transport_contractor_ids]
    
    # Función para obtener solo vehículos de contratistas de transporte
    def get_transport_vehicles():
        transport_contractor_ids = {c.id for c in get_transport_contractors()}
        all_vehicles = vehicle_service.get_all()
        return [v for v in all_vehicles if v.contractor_id in transport_contractor_ids]
    
    tab1, tab2, tab3, tab4 = st.tabs(["Contratistas", "Choferes", "Camiones", "Contenedores"])
    
    with tab1:
        GenericMasterView(
            service=contractor_service, 
            model_class=Contractor, 
            title="Contratistas",
            display_columns=["name", "rut", "phone", "contractor_type"],
            data_source=get_transport_contractors,
            form_config={
                "name": FieldConfig(label="Nombre Empresa", required=True),
                "rut": FieldConfig(label="RUT", required=True),
                "contact_name": FieldConfig(label="Contacto"),
                "phone": FieldConfig(label="Teléfono"),
                "contractor_type": FieldConfig(
                    label="Tipo de Proveedor",
                    widget="enum",
                    enum_class=ContractorType,
                    default=ContractorType.TRANSPORT.value,
                    help="Tipo de servicio que presta el contratista"
                )
            }
        ).render()
        
    with tab2:
        # Drivers - with foreign key to contractor
        GenericMasterView(
            service=driver_service,
            model_class=Driver,
            title="Choferes",
            display_columns=["name", "rut", "license_number", "contractor_id"],
            data_source=get_transport_drivers,
            form_config={
                "name": FieldConfig(label="Nombre Completo", required=True),
                "rut": FieldConfig(label="RUT", required=True),
                "license_number": FieldConfig(label="Nº Licencia", required=True),
                "contractor_id": FieldConfig(
                    label="Contratista",
                    widget="selectbox",
                    options=get_transport_contractors,
                    required=True
                )
            }
        ).render()
        
    with tab3:
        # Vehicles - with foreign key to contractor
        GenericMasterView(
            service=vehicle_service,
            model_class=Vehicle,
            title="Camiones",
            display_columns=["license_plate", "brand", "model", "type", "contractor_id"],
            data_source=get_transport_vehicles,
            form_config={
                "license_plate": FieldConfig(label="Patente", required=True),
                "brand": FieldConfig(label="Marca"),
                "model": FieldConfig(label="Modelo"),
                "year": FieldConfig(label="Año", widget="number_input"),
                "type": FieldConfig(
                    label="Tipo",
                    widget="selectbox",
                    options=VehicleType.choices(),
                    required=True
                ),
                "tare_weight": FieldConfig(
                    label="Tara (kg)", 
                    widget="number_input", 
                    required=True,
                    help="Peso del vehículo vacío en kilogramos"
                ),
                "max_gross_weight": FieldConfig(
                    label="PBV Máximo (kg)", 
                    widget="number_input", 
                    required=True,
                    help="Peso Bruto Vehicular máximo permitido (hasta 55,000 kg)"
                ),
                "contractor_id": FieldConfig(
                    label="Contratista",
                    widget="selectbox",
                    options=get_transport_contractors,
                    required=True
                )
            }
        ).render()

    with tab4:
        # Contenedores (Tolvas) - solo si el servicio está disponible
        if container_service:
            containers_view.render(container_service, contractor_service)
        else:
            st.warning("⚠️ Servicio de contenedores no disponible.")

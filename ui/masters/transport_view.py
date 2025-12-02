import streamlit as st
from models.masters.transport import Contractor
from models.masters.vehicle import Vehicle
from models.masters.driver import Driver
from ui.generic_master_view import GenericMasterView, FieldConfig

def render(driver_service, vehicle_service, contractor_service):
    """
    Vista de gestión de Transporte usando Vistas Genéricas.
    """
    st.header("🚛 Gestión de Transporte")
    
    tab1, tab2, tab3 = st.tabs(["Contratistas", "Choferes", "Camiones"])
    
    with tab1:
        GenericMasterView(
            service=contractor_service, 
            model_class=Contractor, 
            title="Contratistas",
            display_columns=["name", "rut", "phone"],
            form_config={
                "name": FieldConfig(label="Nombre Empresa", required=True),
                "rut": FieldConfig(label="RUT", required=True),
                "contact_name": FieldConfig(label="Contacto"),
                "phone": FieldConfig(label="Teléfono")
            }
        ).render()
        
    with tab2:
        # Drivers - with foreign key to contractor
        GenericMasterView(
            service=driver_service,
            model_class=Driver,
            title="Choferes",
            display_columns=["name", "rut", "license_number", "contractor_id"],
            form_config={
                "name": FieldConfig(label="Nombre Completo", required=True),
                "rut": FieldConfig(label="RUT", required=True),
                "license_number": FieldConfig(label="Nº Licencia", required=True),
                "contractor_id": FieldConfig(
                    label="Contratista",
                    widget="selectbox",
                    options=contractor_service,
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
            form_config={
                "license_plate": FieldConfig(label="Patente", required=True),
                "brand": FieldConfig(label="Marca"),
                "model": FieldConfig(label="Modelo"),
                "year": FieldConfig(label="Año", widget="number_input"),
                "type": FieldConfig(
                    label="Tipo",
                    widget="selectbox",
                    options=[("BATEA", "BATEA"), ("AMPLIROLL", "AMPLIROLL")],
                    required=True
                ),
                "tare_weight": FieldConfig(label="Tara (kg)", widget="number_input", required=True),
                "capacity_wet_tons": FieldConfig(label="Capacidad (tons)", widget="number_input", required=True),
                "contractor_id": FieldConfig(
                    label="Contratista",
                    widget="selectbox",
                    options=contractor_service,
                    required=True
                )
            }
        ).render()

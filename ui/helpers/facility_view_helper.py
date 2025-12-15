"""
Helper function for facilities view with custom validation.
"""
import streamlit as st
from ui.generic_master_view import GenericMasterView, FieldConfig
from domain.processing.entities.facility import Facility
from domain.logistics.entities.vehicle import VehicleType


def _render_facilities_view(facility_service, client_service):
    """
    Render facilities view with custom validation.
    
    Validations:
    - Facilities with only BATEA cannot be link points
    """
    
    class FacilityViewWithValidation(GenericMasterView):
        """Extended GenericMasterView with facility-specific validation."""
        
        def _handle_submit(self, form_data):
            """Override to add custom validation."""
            # Validate link point rule: only BATEA cannot be link points
            if form_data.get('is_link_point'):
                allowed_types = form_data.get('allowed_vehicle_types', '')
                if allowed_types:
                    # Parse CSV string
                    types_list = [t.strip() for t in allowed_types.split(',')]
                    # Check if only BATEA
                    if types_list == ['BATEA'] or (len(types_list) == 1 and 'BATEA' in types_list):
                        st.error("⚠️ Las plantas que solo permiten BATEA no pueden ser puntos de enlace")
                        st.info("💡 Agrega otros tipos de vehículos (AMPLIROLL, etc.) o desmarca 'Punto de Enlace'")
                        return
            
            # Call parent implementation
            super()._handle_submit(form_data)
        
        def _handle_edit_submit(self, form_data):
            """Override to add custom validation for edits."""
            # Same validation for edits
            if form_data.get('is_link_point'):
                allowed_types = form_data.get('allowed_vehicle_types', '')
                if allowed_types:
                    types_list = [t.strip() for t in allowed_types.split(',')]
                    if types_list == ['BATEA'] or (len(types_list) == 1 and 'BATEA' in types_list):
                        st.error("⚠️ Las plantas que solo permiten BATEA no pueden ser puntos de enlace")
                        st.info("💡 Agrega otros tipos de vehículos (AMPLIROLL, etc.) o desmarca 'Punto de Enlace'")
                        return
            
            # Call parent implementation
            super()._handle_edit_submit(form_data)
    
    # Render using extended view
    FacilityViewWithValidation(
        service=facility_service,
        model_class=Facility,
        title="Plantas del Cliente (Instalaciones de Origen)",
        display_columns=["name", "client_id", "address", "allowed_vehicle_types", "is_link_point"],
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
            ),
            "is_link_point": FieldConfig(
                label="¿Es Punto de Enlace?",
                widget="checkbox",
                help="Marcar si esta planta puede actuar como punto intermedio de transferencia. NOTA: Solo plantas con AMPLIROLL pueden ser puntos de enlace."
            )
        }
    ).render()

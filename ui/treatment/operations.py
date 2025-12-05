"""
Treatment Operations Page.

This module acts as an orchestrator for treatment operations,
delegating each tab's logic to its own dedicated module.
"""

import streamlit as st
from ui.styles import apply_industrial_style
from ui.treatment.tabs import reception_view
from ui.treatment.ds4_monitoring import ds4_monitoring_view
from ui.utils.inputs import select_entity


def treatment_operations_page(container):
    """
    Main treatment operations page orchestrator.
    
    Handles plant selection and delegates tab rendering to specialized modules.
    
    Args:
        container: SimpleNamespace with all injected services
    """
    # Extract services from container
    treatment_plant_service = container.treatment_plant_service
    treatment_reception_service = container.treatment_reception_service
    container_service = container.container_service
    logistics_service = container.logistics_service
    pickup_request_service = container.pickup_request_service
    container_tracking_service = getattr(container, 'container_tracking_service', None)
    
    apply_industrial_style()
    st.title("🏭 Operaciones de Tratamiento")
    
    # 1. Context Selection (Plant) - using new helper
    plant_id = select_entity(
        "Seleccione Planta de Trabajo",
        treatment_plant_service,
        empty_message="No hay plantas de tratamiento configuradas."
    )
    if plant_id is None:
        return
    
    st.divider()
    
    # 2. Render Tabs - Each delegated to its own module
    tab_reception, tab_ds4 = st.tabs([
        "📥 Recepción de Lodos", 
        "🧪 Proceso DS4 (Salida)"
    ])
    
    with tab_reception:
        reception_view.render(treatment_reception_service, plant_id)
    
    with tab_ds4:
        ds4_monitoring_view(plant_id, container_service, logistics_service, pickup_request_service, container_tracking_service)
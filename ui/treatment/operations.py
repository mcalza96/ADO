"""
Treatment Operations Page.

This module acts as an orchestrator for treatment operations,
delegating each tab's logic to its own dedicated module.
"""

import streamlit as st
from ui.styles import apply_industrial_style
from ui.treatment.tabs import reception_view
from ui.treatment.ds4_monitoring import (
    _render_container_filling_tab,
    _render_request_form,
    _render_request_history,
    _render_pending_ph_tab
)
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
    tab_reception, tab_llenado, tab_mediciones, tab_solicitar, tab_historial = st.tabs([
        "📥 Recepción de Lodos",
        "📦 Llenado de Contenedores",
        "🧪 Mediciones de pH",
        "📝 Solicitar Retiro", 
        "📋 Historial de Solicitudes"
    ])
    
    with tab_reception:
        reception_view.render(container, plant_id)
    
    with tab_llenado:
        _render_container_filling_tab(plant_id, container_tracking_service)
    
    with tab_mediciones:
        _render_pending_ph_tab(plant_id, container_tracking_service)
    
    with tab_solicitar:
        _render_request_form(plant_id, pickup_request_service)
    
    with tab_historial:
        _render_request_history(plant_id, pickup_request_service)
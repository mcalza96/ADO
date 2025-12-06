"""
Tracking View - Seguimiento de cargas en tiempo real.

Responsabilidad única: Mostrar el estado y seguimiento de cargas activas.
"""

import streamlit as st
from ui.presenters.logistics_presenter import LogisticsPresenter


def tracking_page(container):
    """
    Página de seguimiento de cargas en tiempo real.
    
    Args:
        container: Contenedor de servicios inyectado
    """
    st.title("📍 Seguimiento de Cargas")
    st.markdown("**Actividad:** Monitorear cargas en tiempo real")
    
    # Obtener cargas activas
    loads = _get_active_loads(container)
    
    if not loads:
        st.info("✅ No hay cargas en tránsito")
        return
    
    st.metric("Cargas en Tránsito", len(loads))
    
    for load in loads:
        _render_tracking_card(load)


def _get_active_loads(container):
    """Obtiene las cargas activas en tránsito."""
    try:
        if hasattr(container, 'logistics_app_service'):
            return container.logistics_app_service.get_active_loads()
        elif hasattr(container, 'dispatch_service'):
            return container.dispatch_service.get_loads_by_status("IN_TRANSIT")
    except Exception as e:
        st.warning(f"⚠️ Error al cargar seguimiento: {str(e)}")
    return []


def _render_tracking_card(load):
    """Renderiza una tarjeta de seguimiento para una carga."""
    with st.expander(f"🚛 {load.manifest_code}", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            destination = load.destination_site_id or load.treatment_plant_id or "N/A"
            st.metric("Destino", destination)
            st.metric("Conductor", load.driver_id or "N/A")
        
        with col2:
            weight = f"{load.weight_net:.0f} kg" if load.weight_net else "N/A"
            st.metric("Peso", weight)
            st.metric("Estado", load.status)
        
        with col3:
            dispatch_time = _format_time(load, 'dispatch_time')
            eta = _format_time(load, 'eta')
            
            st.metric("Despachado", dispatch_time)
            st.metric("ETA", eta)


def _format_time(load, attr_name: str) -> str:
    """Formatea un atributo de tiempo de forma segura."""
    if hasattr(load, attr_name):
        time_val = getattr(load, attr_name)
        if time_val:
            return time_val.strftime("%H:%M")
    return "N/A"

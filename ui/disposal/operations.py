"""
Disposal Operations Page.

This module acts as an orchestrator for disposal operations,
delegating each tab's logic to its own dedicated module.
"""

import streamlit as st
from typing import Any

from ui.disposal.tabs import (
    reception_view,
    disposal_view,
    preparation_view,
    closure_view
)


def disposal_operations_page(container) -> None:
    """
    Main disposal operations page orchestrator.
    
    Handles site selection and delegates tab rendering to specialized modules.
    
    Args:
        container: SimpleNamespace con todos los servicios inyectados
    """
    # Extraer servicios del container
    disposal_service = container.disposal_service
    location_service = container.location_service
    site_prep_service = container.site_prep_service
    
    st.title("🏔️ Operaciones de Disposición")
    
    # 1. Context Selection (Site)
    site_id = _render_site_selector(location_service)
    if site_id is None:
        return
    
    st.divider()
    
    # 2. Render Tabs - Each delegated to its own module
    tab_reception, tab_disposal, tab_prep, tab_close = st.tabs([
        "🚛 1. Recepción (Portería)", 
        "🚜 2. Disposición (Campo)",
        "🔧 Preparación",
        "🏁 Cierre"
    ])
    
    with tab_reception:
        reception_view.render(container, site_id)
    
    with tab_disposal:
        disposal_view.render(container, site_id)
    
    with tab_prep:
        preparation_view.render(site_prep_service, site_id)
    
    with tab_close:
        closure_view.render(site_prep_service, site_id)


def _render_site_selector(location_service: Any) -> int | None:
    """
    Render the site selector and return the selected site ID.
    
    Returns:
        The selected site ID, or None if no sites are configured.
    """
    try:
        sites = location_service.get_all_sites()
    except Exception as e:
        st.error(f"Error al cargar predios: {e}")
        return None
    
    if not sites:
        st.warning("No hay predios configurados.")
        return None
    
    s_opts = {s.name: s.id for s in sites}
    sel_site_name = st.selectbox("📍 Seleccione Predio de Trabajo", list(s_opts.keys()))
    
    return s_opts[sel_site_name]


"""
Disposal Preparation Tab View.

Handles the site preparation and pre-work registration
for disposal operations (DO-06 to DO-16).
"""

import streamlit as st
import datetime
from typing import Any


def render(site_prep_service: Any, site_id: int) -> None:
    """
    Render the site preparation tab.
    
    Args:
        site_prep_service: Service for managing site preparation events
        site_id: ID of the selected disposal site
    """
    st.subheader("🔧 Registro de Labores Previas (DO-06 a DO-16)")
    
    _render_event_form(site_prep_service, site_id)
    st.divider()
    _render_event_history(site_prep_service, site_id)


def _render_event_form(site_prep_service: Any, site_id: int) -> None:
    """Render the form to register site preparation events."""
    with st.form("site_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            evt_type = st.selectbox("Tipo de Labor", [
                "Preparación de Suelo (Arado)", 
                "Rastraje",
                "Control de Vectores Inicial",
                "Habilitación de Caminos",
                "Construcción de Pretiles"
            ])
            evt_date = st.date_input("Fecha de Labor", datetime.date.today())
        
        with col2:
            evt_desc = st.text_area("Descripción / Observaciones")
        
        if st.form_submit_button("📝 Registrar Labor"):
            _handle_event_submit(site_prep_service, site_id, evt_type, evt_date, evt_desc)


def _handle_event_submit(
    site_prep_service: Any,
    site_id: int,
    evt_type: str,
    evt_date: datetime.date,
    evt_desc: str
) -> None:
    """Handle the event registration form submission."""
    try:
        site_prep_service.register_site_event(
            site_id, 
            evt_type, 
            datetime.datetime.combine(evt_date, datetime.time(0, 0)), 
            evt_desc
        )
        st.success("✅ Labor registrada correctamente.")
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")


def _render_event_history(site_prep_service: Any, site_id: int) -> None:
    """Render the history of site preparation events."""
    st.markdown("### 📋 Historial de Labores")
    
    try:
        events = site_prep_service.get_site_events(site_id)
        if events:
            for evt in events:
                st.text(
                    f"{evt.event_date} | {evt.event_type} | "
                    f"{evt.description or 'Sin descripción'}"
                )
        else:
            st.info("No hay labores registradas para este predio.")
    except Exception as e:
        st.error(f"Error al cargar historial: {e}")

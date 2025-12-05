"""
Disposal Closure Tab View.

Handles the operational closure functionality
for disposal operations.
"""

import streamlit as st
import datetime
from typing import Any


def render(site_prep_service: Any, site_id: int) -> None:
    """
    Render the operational closure tab.
    
    Args:
        site_prep_service: Service for managing site events (used for closures)
        site_id: ID of the selected disposal site
    """
    st.subheader("🏁 Cierre Operativo de Faena")
    
    _render_closure_form(site_prep_service, site_id)


def _render_closure_form(site_prep_service: Any, site_id: int) -> None:
    """Render the operational closure form."""
    with st.form("closure_form"):
        c_date = st.date_input("Fecha de Cierre", datetime.date.today())
        responsible = st.text_input("Responsable de Cierre")
        
        check_sector = st.checkbox("Cierre de Paño (Sector Completo)")
        check_day = st.checkbox("Cierre de Faena (Diario)")
        
        obs = st.text_area("Observaciones de Cierre")
        
        if st.form_submit_button("🔒 Registrar Cierre"):
            _handle_closure_submit(
                site_prep_service, site_id, c_date,
                responsible, check_sector, check_day, obs
            )


def _handle_closure_submit(
    site_prep_service: Any,
    site_id: int,
    c_date: datetime.date,
    responsible: str,
    check_sector: bool,
    check_day: bool,
    obs: str
) -> None:
    """Handle the closure form submission."""
    try:
        desc = (
            f"Responsable: {responsible} | "
            f"Paño: {check_sector} | "
            f"Faena: {check_day} | "
            f"Obs: {obs}"
        )
        site_prep_service.register_site_event(
            site_id, 
            "Cierre Operativo", 
            datetime.datetime.combine(c_date, datetime.time(23, 59)), 
            desc
        )
        st.success("✅ Cierre operativo registrado correctamente.")
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

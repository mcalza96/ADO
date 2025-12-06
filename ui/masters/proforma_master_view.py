"""
Vista de Gestión del Maestro de Proformas (Estados de Pago).

Este módulo contiene la interfaz gráfica para administrar las proformas,
que representan los ciclos financieros mensuales del 19 al 18.

Autor: Senior Frontend Engineer - ERP Team
Fecha: 2025-12-05
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from container import get_container


# ==============================================================================
# CONSTANTS
# ==============================================================================

MONTH_NAMES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render(proforma_repo=None):
    """
    Vista principal del Maestro de Proformas.
    
    Args:
        proforma_repo: ProformaRepository instance
    """
    st.subheader("�� Maestro de Proformas")
    st.caption("Ciclo financiero: día 19 → día 18 del mes siguiente")
    
    # Get repository from container if not provided
    if proforma_repo is None:
        container = get_container()
        proforma_repo = container.proforma_repo
    
    # Initialize session state
    if 'proforma_success_msg' not in st.session_state:
        st.session_state.proforma_success_msg = None
    if 'proforma_error_msg' not in st.session_state:
        st.session_state.proforma_error_msg = None
    if 'proforma_editing_id' not in st.session_state:
        st.session_state.proforma_editing_id = None
    
    # Show status messages
    if st.session_state.proforma_success_msg:
        st.success(st.session_state.proforma_success_msg)
        st.session_state.proforma_success_msg = None
    
    if st.session_state.proforma_error_msg:
        st.error(st.session_state.proforma_error_msg)
        st.session_state.proforma_error_msg = None
    
    # Fetch proformas
    try:
        proformas = proforma_repo.get_all(include_closed=True)
    except Exception as e:
        st.error(f"❌ Error cargando proformas: {e}")
        return
    
    # Check if we're in editing mode
    editing_id = st.session_state.proforma_editing_id
    
    if editing_id:
        # Show edit form
        proforma = next((p for p in proformas if p.id == editing_id), None)
        if proforma:
            _render_edit_mode(proforma, proforma_repo)
        else:
            st.session_state.proforma_editing_id = None
            st.rerun()
    else:
        # Show table view
        _render_table_view(proformas, proforma_repo)


def _render_table_view(proformas, proforma_repo):
    """Renderiza la vista de tabla con proformas."""
    
    # Action buttons row
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Nueva Proforma", type="primary", use_container_width=True):
            st.session_state.proforma_editing_id = "new"
            st.rerun()
    
    if not proformas:
        st.info("📭 No hay proformas registradas. Cree la primera proforma.")
        return
    
    # Build table data
    table_data = []
    for p in proformas:
        status = "🔒 Cerrada" if p.is_closed else "📝 Abierta"
        month_name = MONTH_NAMES.get(p.period_month, str(p.period_month))
        
        table_data.append({
            "id": p.id,
            "Código": p.proforma_code,
            "Período": f"{month_name} {p.period_year}",
            "UF": f"${p.uf_value:,.0f}",
            "Petróleo": f"${p.fuel_price:,.0f}",
            "Ciclo": f"{p.cycle_start_date} → {p.cycle_end_date}",
            "Estado": status,
            "is_closed": p.is_closed
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table
    st.dataframe(
        df[["Código", "Período", "UF", "Petróleo", "Ciclo", "Estado"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Edit/Close buttons below table
    st.divider()
    
    # Filter only open proformas for actions
    open_proformas = [p for p in proformas if not p.is_closed]
    
    if open_proformas:
        st.markdown("**Acciones:**")
        
        cols = st.columns(len(open_proformas))
        for i, p in enumerate(open_proformas):
            with cols[i]:
                month_name = MONTH_NAMES.get(p.period_month, str(p.period_month))
                st.markdown(f"**{p.proforma_code}**")
                
                col_edit, col_close = st.columns(2)
                with col_edit:
                    if st.button("✏️ Editar", key=f"proforma_edit_{p.id}", use_container_width=True):
                        st.session_state.proforma_editing_id = p.id
                        st.rerun()
                
                with col_close:
                    if st.button("🔒 Cerrar", key=f"proforma_close_{p.id}", use_container_width=True):
                        st.session_state.proforma_editing_id = f"close_{p.id}"
                        st.rerun()
    else:
        st.info("No hay proformas abiertas. Cree una nueva para comenzar.")


def _render_edit_mode(proforma, proforma_repo):
    """Renderiza el modo de edición de una proforma."""
    
    # Check if it's a close action
    editing_id = st.session_state.proforma_editing_id
    if isinstance(editing_id, str) and editing_id.startswith("close_"):
        _render_close_confirmation(proforma, proforma_repo)
        return
    
    # Check if it's a new proforma
    if editing_id == "new":
        _render_new_proforma_form(proforma_repo)
        return
    
    # Edit existing proforma
    if proforma.is_closed:
        st.warning("⚠️ Esta proforma está cerrada y no se puede editar.")
        if st.button("← Volver"):
            st.session_state.proforma_editing_id = None
            st.rerun()
        return
    
    month_name = MONTH_NAMES.get(proforma.period_month, str(proforma.period_month))
    st.markdown(f"### ✏️ Editar {proforma.proforma_code}")
    st.caption(f"Período: {month_name} {proforma.period_year} | Ciclo: {proforma.cycle_start_date} → {proforma.cycle_end_date}")
    
    with st.form(f"edit_proforma_{proforma.id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_uf = st.number_input(
                "Valor UF (CLP)",
                min_value=0.01,
                max_value=100000.0,
                value=float(proforma.uf_value),
                step=100.0,
                help="Valor de la UF al día 18 del ciclo"
            )
        
        with col2:
            new_fuel = st.number_input(
                "Precio Petróleo (CLP/L)",
                min_value=0.01,
                max_value=10000.0,
                value=float(proforma.fuel_price),
                step=10.0,
                help="Precio promedio del diésel en el período"
            )
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            try:
                proforma.uf_value = new_uf
                proforma.fuel_price = new_fuel
                proforma_repo.update(proforma)
                st.session_state.proforma_success_msg = f"✅ {proforma.proforma_code} actualizada"
                st.session_state.proforma_editing_id = None
                st.rerun()
            except Exception as e:
                st.session_state.proforma_error_msg = f"❌ Error: {e}"
                st.rerun()
        
        if cancelled:
            st.session_state.proforma_editing_id = None
            st.rerun()


def _render_new_proforma_form(proforma_repo):
    """Renderiza el formulario para crear una nueva proforma."""
    st.markdown("### ➕ Nueva Proforma")
    
    # Back button
    if st.button("← Volver"):
        st.session_state.proforma_editing_id = None
        st.rerun()
    
    # Get current open proforma to suggest next period
    current_open = proforma_repo.get_current_open()
    
    if current_open:
        next_month = current_open.period_month + 1
        next_year = current_open.period_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        default_year = next_year
        default_month = next_month
        default_uf = current_open.uf_value
        default_fuel = current_open.fuel_price
    else:
        today = date.today()
        default_year = today.year
        default_month = today.month
        default_uf = 37500.0
        default_fuel = 1250.0
    
    with st.form("new_proforma_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.selectbox(
                "Año",
                options=list(range(2024, 2028)),
                index=list(range(2024, 2028)).index(default_year) if default_year in range(2024, 2028) else 1
            )
            uf_value = st.number_input(
                "Valor UF (CLP)",
                min_value=0.01,
                max_value=100000.0,
                value=default_uf,
                step=100.0
            )
        
        with col2:
            month = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                format_func=lambda x: MONTH_NAMES[x],
                index=default_month - 1
            )
            fuel_price = st.number_input(
                "Precio Petróleo (CLP/L)",
                min_value=0.01,
                max_value=10000.0,
                value=default_fuel,
                step=10.0
            )
        
        # Preview
        from domain.finance.entities.finance_entities import Proforma
        preview_code = Proforma.generate_code(year, month)
        preview_start, preview_end = Proforma.calculate_cycle_dates(year, month)
        st.info(f"📋 Código: **{preview_code}** | Ciclo: {preview_start} → {preview_end}")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Crear", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            # Check if already exists
            existing = proforma_repo.get_by_period(year, month)
            if existing:
                st.session_state.proforma_error_msg = f"❌ Ya existe {existing.proforma_code}"
                st.rerun()
            else:
                try:
                    proforma_repo.save(year=year, month=month, uf_value=uf_value, fuel_price=fuel_price)
                    st.session_state.proforma_success_msg = f"✅ {preview_code} creada"
                    st.session_state.proforma_editing_id = None
                    st.rerun()
                except Exception as e:
                    st.session_state.proforma_error_msg = f"❌ Error: {e}"
                    st.rerun()
        
        if cancelled:
            st.session_state.proforma_editing_id = None
            st.rerun()


def _render_close_confirmation(proforma, proforma_repo):
    """Renderiza confirmación para cerrar una proforma."""
    st.markdown(f"### 🔒 Cerrar {proforma.proforma_code}")
    
    # Back button
    if st.button("← Volver"):
        st.session_state.proforma_editing_id = None
        st.rerun()
    
    month_name = MONTH_NAMES.get(proforma.period_month, str(proforma.period_month))
    st.warning(f"¿Está seguro de cerrar la proforma de **{month_name} {proforma.period_year}**?")
    
    st.markdown(f"""
    **Valores actuales:**
    - UF: ${proforma.uf_value:,.0f}
    - Petróleo: ${proforma.fuel_price:,.0f}/L
    
    **Al cerrar:**
    - ✅ Los valores quedan inmutables
    - ✅ Se crea automáticamente la siguiente proforma
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔒 Confirmar Cierre", type="primary", use_container_width=True):
            try:
                from domain.finance.entities.finance_entities import Proforma
                next_month = proforma.period_month + 1
                next_year = proforma.period_year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_code = Proforma.generate_code(next_year, next_month)
                
                proforma_repo.close_proforma(proforma.id, auto_create_next=True)
                st.session_state.proforma_success_msg = f"✅ {proforma.proforma_code} cerrada. Creada {next_code}"
                st.session_state.proforma_editing_id = None
                st.rerun()
            except Exception as e:
                st.session_state.proforma_error_msg = f"❌ Error: {e}"
                st.rerun()
    
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.proforma_editing_id = None
            st.rerun()

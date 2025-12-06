"""
Disposal Field Tab View.

Handles the field disposal (incorporation) functionality
for disposal operations.

Permite seleccionar la parcela/sector donde se va a disponer la carga.
"""

import streamlit as st
from typing import Any, List


def render(disposal_service: Any, site_id: int) -> None:
    """
    Render the field disposal tab.
    
    Args:
        disposal_service: Service for managing disposal operations
        site_id: ID of the selected disposal site
    """
    st.subheader("🚜 Disposición en Campo")
    st.markdown("**Rol:** Tractorista/Operador | **Acción:** Seleccionar parcela y confirmar disposición")
    
    if st.button("🔄 Actualizar Cargas Disponibles", key="refresh_disposal"):
        st.rerun()
    
    st.divider()
    
    arrived_loads = _get_arrived_loads(disposal_service, site_id)
    
    if not arrived_loads:
        st.info("✅ No hay cargas recepcionadas pendientes de disposición.")
        return
    
    # Obtener parcelas disponibles para el selector
    plots = _get_plots_for_site(disposal_service, site_id)
    
    if not plots:
        st.warning("⚠️ No hay parcelas configuradas para este predio. Configure parcelas en el módulo de Configuración.")
        return
    
    st.success(f"📦 Hay {len(arrived_loads)} carga(s) lista(s) para disposición.")
    
    for load in arrived_loads:
        _render_disposal_card(disposal_service, load, plots)


def _get_arrived_loads(disposal_service: Any, site_id: int) -> list:
    """Get loads ready for disposal (Status: AT_DESTINATION) for the given site."""
    try:
        # Intentar usar método específico para disposición
        if hasattr(disposal_service, 'get_pending_disposal_loads'):
            return disposal_service.get_pending_disposal_loads(site_id)
        
        # Fallback: buscar directamente en load_repo
        load_repo = disposal_service.load_repo
        loads = load_repo.get_by_status('AT_DESTINATION')
        return [l for l in loads if l.destination_site_id == site_id]
    except Exception as e:
        st.error(f"Error al cargar cargas para disposición: {e}")
        return []


def _get_plots_for_site(disposal_service: Any, site_id: int) -> List[Any]:
    """Get available plots/sectors for the site."""
    try:
        return disposal_service.get_plots_by_site(site_id)
    except Exception as e:
        st.error(f"Error al cargar parcelas: {e}")
        return []


def _render_disposal_card(disposal_service: Any, load: Any, plots: List[Any]) -> None:
    """Render a single disposal card with form."""
    # Obtener peso neto de cualquiera de los dos campos
    peso_neto = load.weight_net or load.net_weight or 0
    
    with st.expander(
        f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - "
        f"Peso: {peso_neto:.0f} kg",
        expanded=True
    ):
        _render_load_summary(load)
        st.divider()
        _render_disposal_form(disposal_service, load, plots)


def _render_load_summary(load: Any) -> None:
    """Muestra resumen de la carga (datos del transporte y recepción)."""
    st.markdown("#### 📋 Resumen de Carga")
    
    # Obtener peso neto de cualquiera de los dos campos
    peso_neto = load.weight_net or load.net_weight or 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**🎫 Ticket:** {load.ticket_number or 'N/A'}")
        st.markdown(f"**📄 Guía:** {load.guide_number or 'N/A'}")
        st.markdown(f"**⚖️ Peso Neto:** {peso_neto:.0f} kg")
    
    with col2:
        st.markdown(f"**🧪 pH:** {load.quality_ph or 'N/A'}")
        st.markdown(f"**💧 Humedad:** {load.quality_humidity or 'N/A'}%" if load.quality_humidity else "**💧 Humedad:** N/A")
        arrival = load.arrival_time
        if arrival:
            if hasattr(arrival, 'strftime'):
                st.markdown(f"**🕐 Llegada:** {arrival.strftime('%H:%M')}")
            else:
                st.markdown(f"**🕐 Llegada:** {str(arrival)[:16]}")
        else:
            st.markdown("**🕐 Llegada:** N/A")
    
    with col3:
        st.markdown(f"**📊 Estado:** `{load.status}`")
        if load.reception_observations:
            st.markdown(f"**📝 Obs:** {load.reception_observations}")


def _render_disposal_form(disposal_service: Any, load: Any, plots: List[Any]) -> None:
    """Render the disposal form with plot selector."""
    st.markdown("#### 🌾 Seleccionar Destino de Disposición")
    
    with st.form(f"disposal_form_{load.id}"):
        # Selector de parcela
        plot_options = {p.name: p.id for p in plots}
        
        selected_plot_name = st.selectbox(
            "📍 Parcela / Sector",
            options=list(plot_options.keys()),
            key=f"plot_{load.id}",
            help="Seleccione la parcela donde se va a disponer la carga"
        )
        
        selected_plot_id = plot_options.get(selected_plot_name)
        
        # Mostrar info de la parcela seleccionada
        selected_plot = next((p for p in plots if p.id == selected_plot_id), None)
        if selected_plot and selected_plot.area_hectares:
            st.caption(f"Área de parcela: {selected_plot.area_hectares:.2f} hectáreas")
        
        if st.form_submit_button("✅ Confirmar Disposición", type="primary"):
            _handle_disposal_submit(disposal_service, load.id, selected_plot_id)


def _handle_disposal_submit(
    disposal_service: Any,
    load_id: int,
    plot_id: int
) -> None:
    """Handle the disposal form submission."""
    try:
        disposal_service.execute_disposal(
            load_id=load_id,
            plot_id=plot_id
        )
        st.success(f"✅ Carga #{load_id} dispuesta exitosamente. Viaje completado.")
        st.rerun()
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

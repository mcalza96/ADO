"""
Disposal Reception Tab View.

Handles the reception functionality at the weighbridge/gate
for disposal operations.

Muestra cargas con status EN_ROUTE_DESTINATION que van hacia el predio seleccionado.
El operario verifica los datos del transporte y registra el pH de verificación.
"""

import streamlit as st
from typing import Any


from domain.disposal.application.disposal_app_service import DisposalReceptionDTO

def render(container: Any, site_id: int) -> None:
    """
    Render the reception tab for disposal operations.
    
    Args:
        container: Dependency container
        site_id: ID of the selected disposal site
    """
    st.subheader("🚛 Recepción en Portería")
    st.markdown("**Rol:** Operario de Báscula | **Acción:** Verificar datos y registrar pH")
    
    if st.button("🔄 Actualizar Cargas en Ruta", key="refresh_reception"):
        st.rerun()
    
    st.divider()
    
    # Use App Service if available, fallback to legacy service
    app_service = getattr(container, 'disposal_app_service', None)
    legacy_service = getattr(container, 'disposal_service', None)
    
    dispatched_loads = []
    if app_service:
        dispatched_loads = app_service.get_incoming_loads(site_id)
    elif legacy_service:
        dispatched_loads = _get_dispatched_loads_legacy(legacy_service, site_id)
    
    if not dispatched_loads:
        st.info("✅ No hay cargas en ruta hacia este predio.")
        return
    
    st.success(f"📦 Hay {len(dispatched_loads)} carga(s) en ruta esperando recepción.")
    
    for load in dispatched_loads:
        _render_load_reception_card(container, load)


def _get_dispatched_loads_legacy(disposal_service: Any, site_id: int) -> list:
    """Legacy method to get loads."""
    try:
        # Usar el nuevo método que filtra por destino y status correcto
        if hasattr(disposal_service, 'get_in_transit_loads_by_destination_site'):
            return disposal_service.get_in_transit_loads_by_destination_site(site_id)
        
        # Fallback: usar load_repo directamente
        load_repo = disposal_service.load_repo
        
        # Intentar con el nuevo status primero
        dispatched_loads = load_repo.get_by_status('EN_ROUTE_DESTINATION')
        filtered = [l for l in dispatched_loads if l.destination_site_id == site_id]
        
        # Si no hay resultados, intentar con status legacy
        if not filtered:
            dispatched_loads = load_repo.get_by_status('Dispatched')
            filtered = [l for l in dispatched_loads if l.destination_site_id == site_id]
        
        return filtered
    except Exception as e:
        st.error(f"Error al cargar cargas despachadas: {e}")
        return []


def _render_load_reception_card(container: Any, load: Any) -> None:
    """Render a single load reception card with form."""
    with st.expander(
        f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'}",
        expanded=True
    ):
        _render_transport_data(load)
        st.divider()
        _render_reception_form(container, load)


def _render_transport_data(load: Any) -> None:
    """Muestra los datos que vienen del módulo de transporte (solo lectura)."""
    st.markdown("#### 📋 Datos del Transporte (desde despacho)")
    
    # Obtener peso neto de cualquiera de los dos campos
    peso_neto = load.weight_net or load.net_weight or 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎫 Ticket", load.ticket_number or "N/A")
        st.metric("⚖️ Peso Neto", f"{peso_neto:.0f} kg")
    
    with col2:
        st.metric("📄 Guía", load.guide_number or "N/A")
        st.metric("🧪 pH (origen)", f"{load.quality_ph or 'N/A'}")
    
    with col3:
        st.metric("💧 Humedad", f"{load.quality_humidity or 'N/A'}%" if load.quality_humidity else "N/A")
        dispatch_time = load.dispatch_time
        if dispatch_time:
            if hasattr(dispatch_time, 'strftime'):
                st.metric("🕐 Despacho", dispatch_time.strftime("%H:%M"))
            else:
                st.metric("🕐 Despacho", str(dispatch_time)[:16])
        else:
            st.metric("🕐 Despacho", "N/A")


def _render_reception_form(container: Any, load: Any) -> None:
    """Render the reception form - solo captura pH de verificación."""
    st.markdown("#### ✅ Verificación en Recepción")
    
    with st.form(f"reception_form_{load.id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            ph_reception = st.number_input(
                "🧪 pH (verificación en destino)",
                min_value=0.0,
                max_value=14.0,
                value=float(load.quality_ph or 7.0),
                step=0.1,
                key=f"ph_{load.id}",
                help="pH medido al recibir la carga en el predio"
            )
        
        with col2:
            observation = st.text_area(
                "📝 Observaciones (opcional)",
                placeholder="Ej: Olor normal, consistencia adecuada...",
                key=f"obs_{load.id}",
                height=100
            )
        
        if st.form_submit_button("✅ Confirmar Recepción", type="primary"):
            _handle_reception_submit(container, load.id, ph_reception, observation)


def _handle_reception_submit(
    container: Any,
    load_id: int,
    ph: float,
    observation: str | None
) -> None:
    """Handle the reception form submission."""
    try:
        # Use App Service if available
        if hasattr(container, 'disposal_app_service'):
            dto = DisposalReceptionDTO(
                load_id=load_id,
                ph=ph,
                observation=observation
            )
            container.disposal_app_service.register_arrival(dto)
        else:
            # Fallback
            container.disposal_service.register_arrival(
                load_id=load_id,
                ph=ph,
                observation=observation if observation else None
            )
        
        st.success(f"✅ Carga #{load_id} recepcionada correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al registrar recepción: {e}")
        st.success(
            f"✅ Carga #{load_id} recepcionada exitosamente. "
            "Ahora está disponible para disposición en campo."
        )
        st.rerun()
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

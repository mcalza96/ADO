"""
Treatment Reception Tab View.

Handles the sludge reception functionality for treatment operations,
including displaying pending loads and processing reception.

Muestra cargas con status EN_ROUTE_DESTINATION que van hacia la planta seleccionada.
"""

import streamlit as st
import datetime
from typing import Any


from domain.processing.application.treatment_app_service import TreatmentReceptionDTO

def render(container: Any, plant_id: int) -> None:
    """
    Render the sludge reception tab.
    
    Args:
        container: Dependency container
        plant_id: ID of the selected treatment plant
    """
    st.subheader("📥 Bandeja de Entrada (Cargas en Ruta)")
    
    if st.button("🔄 Actualizar Bandeja"):
        st.rerun()
    
    # Use App Service if available, fallback to legacy service
    app_service = getattr(container, 'treatment_app_service', None)
    legacy_service = getattr(container, 'treatment_reception_service', None)
    
    pending = []
    if app_service:
        pending = app_service.get_incoming_loads(plant_id)
    elif legacy_service:
        pending = _get_in_transit_loads_legacy(legacy_service, plant_id)
    
    if not pending:
        st.info("No hay cargas en ruta hacia esta planta.")
        return
    
    st.success(f"Hay {len(pending)} cargas en ruta esperando recepción.")
    
    for load in pending:
        _render_load_reception_card(container, load)


def _get_in_transit_loads_legacy(reception_service: Any, plant_id: int) -> list:
    """Legacy method to get loads."""
    try:
        # Intentar usar el nuevo método del servicio de logística
        if hasattr(reception_service, 'get_in_transit_loads_by_treatment_plant'):
            return reception_service.get_in_transit_loads_by_treatment_plant(plant_id)
        
        # Fallback: acceder directamente al load_repo
        if hasattr(reception_service, 'load_repo'):
            load_repo = reception_service.load_repo
            
            # Intentar con el nuevo status primero
            in_transit = load_repo.get_by_status('EN_ROUTE_DESTINATION')
            filtered = [l for l in in_transit if l.destination_treatment_plant_id == plant_id]
            
            # Si no hay resultados, intentar con el método legacy
            if not filtered:
                return reception_service.get_pending_reception_loads(plant_id)
            
            return filtered
        
        # Último fallback: usar el método existente
        return reception_service.get_pending_reception_loads(plant_id)
    except Exception as e:
        st.error(f"Error al cargar cargas en ruta: {e}")
        return []


def _render_load_reception_card(container: Any, load: Any) -> None:
    """Render a single load reception card with form."""
    peso_neto = load.weight_net or load.net_weight or 0
    with st.expander(
        f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - {peso_neto:.0f} kg", 
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
        st.metric("💧 Humedad (origen)", f"{load.quality_humidity or 'N/A'}%" if load.quality_humidity else "N/A")
        dispatch_time = load.dispatch_time
        if dispatch_time:
            if hasattr(dispatch_time, 'strftime'):
                st.metric("🕐 Despacho", dispatch_time.strftime("%H:%M"))
            else:
                st.metric("🕐 Despacho", str(dispatch_time)[:16])
        else:
            st.metric("🕐 Despacho", "N/A")


def _render_reception_form(container: Any, load: Any) -> None:
    """Render the reception form for a load."""
    st.markdown("#### ✅ Verificación en Recepción")
    
    with st.form(f"reception_form_{load.id}"):
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            rec_time = st.time_input(
                "🕐 Hora Ingreso Real", 
                datetime.datetime.now().time()
            )
        with col_t2:
            dis_time = st.time_input(
                "🕐 Hora Descarga Foso", 
                datetime.datetime.now().time()
            )
        
        st.markdown("##### 🧪 pH de Llegada")
        st.info(
            "📍 **pH Origen (despacho):** {:.1f} → Registre el **pH de llegada** para verificar la estabilidad durante el transporte.".format(
                load.quality_ph or 0
            )
        )
        
        col_ph1, col_ph2 = st.columns(2)
        
        with col_ph1:
            arrival_ph = st.number_input(
                "🧪 pH de Llegada *", 
                min_value=0.0, 
                max_value=14.0, 
                step=0.1, 
                value=float(load.quality_ph or 7.0),
                help="pH medido al recibir la carga en planta de tratamiento"
            )
        
        with col_ph2:
            humidity = st.number_input(
                "💧 Humedad (%) (verificación)", 
                min_value=0.0, 
                max_value=100.0, 
                step=0.1, 
                value=float(load.quality_humidity or 80.0),
                help="Humedad medida al recibir la carga en planta"
            )
        
        observation = st.text_area(
            "📝 Observaciones (opcional)",
            placeholder="Ej: Material con consistencia normal, sin olores atípicos...",
            key=f"obs_{load.id}",
            height=80
        )
        
        if st.form_submit_button("✅ Confirmar Recepción", type="primary"):
            _handle_reception_submit(
                container, load.id, rec_time, dis_time, arrival_ph, humidity, observation
            )


def _handle_reception_submit(
    container: Any,
    load_id: int,
    rec_time: datetime.time,
    dis_time: datetime.time,
    arrival_ph: float,
    humidity: float,
    observation: str | None = None
) -> None:
    """Handle the reception form submission."""
    try:
        # Combine with today's date for MVP simplicity
        today = datetime.date.today()
        rec_dt = datetime.datetime.combine(today, rec_time)
        dis_dt = datetime.datetime.combine(today, dis_time)
        
        # Use App Service if available
        if hasattr(container, 'treatment_app_service'):
            dto = TreatmentReceptionDTO(
                load_id=load_id,
                reception_time=rec_dt,
                discharge_time=dis_dt,
                ph=arrival_ph,
                humidity=humidity,
                observation=observation,
                arrival_ph=arrival_ph
            )
            container.treatment_app_service.execute_reception(dto)
        else:
            # Fallback
            container.treatment_reception_service.execute_reception(
                load_id=load_id, 
                reception_time=rec_dt, 
                discharge_time=dis_dt, 
                ph=arrival_ph,
                humidity=humidity,
                observation=observation if observation else None,
                arrival_ph=arrival_ph
            )
            
        st.success(
            f"✅ Carga #{load_id} recepcionada y completada exitosamente. "
            "El viaje ha finalizado."
        )
        st.rerun()
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

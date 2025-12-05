"""
Field Reception View - Recepción en campo/predio.

Responsabilidad única: Gestionar el proceso de recepción de cargas
en el destino (Gate In).
"""

import streamlit as st
from pydantic import ValidationError
from domain.shared.commands import RegisterArrivalCommand


def field_reception_page(container):
    """
    Página de recepción en predio - Gate In.
    
    Args:
        container: Contenedor de servicios inyectado
    """
    st.title("📦 Recepción en Predio")
    st.markdown("**Actividad:** Registrar llegada y pesaje en báscula")
    
    # Obtener cargas en tránsito
    loads_in_transit = _get_loads_in_transit(container)
    
    if not loads_in_transit:
        st.info("✅ No hay cargas en tránsito")
        return
    
    st.success(f"📦 {len(loads_in_transit)} carga(s) en tránsito")
    
    for load in loads_in_transit:
        _render_load_reception_card(container, load)


def _get_loads_in_transit(container):
    """Obtiene las cargas con estado IN_TRANSIT."""
    try:
        if hasattr(container, 'dispatch_service'):
            return container.dispatch_service.get_loads_by_status("IN_TRANSIT")
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar las cargas en tránsito: {str(e)}")
    return []


def _render_load_reception_card(container, load):
    """Renderiza una tarjeta de recepción para una carga específica."""
    with st.expander(f"🚛 Carga #{load.id} - {load.manifest_code}", expanded=True):
        st.markdown(f"**Conductor:** {load.driver_id}")
        st.markdown(f"**Vehículo:** {load.vehicle_id}")
        st.markdown(f"**Peso Estimado:** {load.weight_net:.0f} kg")
        
        form_data = _render_reception_form(load)
        
        if form_data:
            _process_reception(container, load.id, form_data)


def _render_reception_form(load):
    """Renderiza el formulario de recepción para una carga."""
    with st.form(f"reception_{load.id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            arrival_time = st.datetime_input(
                "Hora de Llegada",
                value=None
            )
            weight_gross = st.number_input(
                "Peso Bruto (kg)",
                min_value=0.0,
                max_value=50000.0
            )
        
        with col2:
            ph = st.number_input(
                "pH (opcional)",
                min_value=4.0,
                max_value=10.0,
                value=7.0,
                step=0.1
            )
            humidity = st.number_input(
                "Humedad % (opcional)",
                min_value=0.0,
                max_value=100.0,
                value=75.0,
                step=0.1
            )
        
        observation = st.text_area("Observaciones")
        
        submit = st.form_submit_button("✅ Registrar Llegada", type="primary")
    
    if submit:
        return {
            'arrival_time': arrival_time,
            'weight_gross': weight_gross,
            'ph': ph,
            'humidity': humidity,
            'observation': observation
        }
    
    return None


def _process_reception(container, load_id: int, form_data: dict):
    """Procesa el registro de llegada."""
    try:
        command = RegisterArrivalCommand(
            load_id=load_id,
            arrival_time=form_data['arrival_time'],
            weight_gross=form_data['weight_gross'] if form_data['weight_gross'] > 0 else None,
            ph=form_data['ph'] if form_data['ph'] else None,
            humidity=form_data['humidity'] if form_data['humidity'] else None,
            observation=form_data['observation'] if form_data['observation'] else None
        )
        
        # Usar dispatch_service directamente (no logistics.dispatch_service)
        success = container.dispatch_service.register_arrival(
            load_id=command.load_id,
            weight_gross=command.weight_gross,
            ph=command.ph,
            humidity=command.humidity,
            observation=command.observation
        )
        
        if success:
            st.success(f"✅ Llegada registrada para carga {load_id}")
            st.rerun()
        else:
            st.error("❌ Error al registrar llegada")
            
    except ValidationError as e:
        st.error("❌ Errores de validación:")
        for error in e.errors():
            st.error(f"**{error['loc'][0]}**: {error['msg']}")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

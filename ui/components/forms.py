"""
Dynamic Forms System - Patrón Registry para Formularios Extensibles

Sistema de registro de formularios que permite agregar nuevos tipos de verificadores
sin modificar la lógica core del Inbox.

Uso:
    @register_form("nuevo_verificador")
    def render_nuevo_form(load_id: int) -> Optional[Dict]:
        # Renderizar formulario
        # Retornar dict para attributes o None
"""
import streamlit as st
from typing import Dict, Callable, Optional, Any
from datetime import datetime


# ============================================================================
# TYPE ALIASES
# ============================================================================

FormRenderer = Callable[[int], Optional[Dict[str, Any]]]


# ============================================================================
# FORM REGISTRY (Patrón Strategy/Factory)
# ============================================================================

FORM_REGISTRY: Dict[str, FormRenderer] = {}


def register_form(verifier_key: str):
    """
    Decorator para registrar un formulario en el registry.
    
    Example:
        @register_form("lab_analysis_result")
        def render_lab_form(load_id: int) -> Optional[Dict]:
            # ... implementación
            return data_dict
    """
    def decorator(func: FormRenderer):
        FORM_REGISTRY[verifier_key] = func
        return func
    return decorator


def get_form_renderer(verifier_key: str) -> Optional[FormRenderer]:
    """
    Obtiene el renderer para un verificador específico.
    
    Args:
        verifier_key: Clave del verificador (ej: "lab_analysis_result")
    
    Returns:
        Función renderer o None si no está registrada
    """
    return FORM_REGISTRY.get(verifier_key)


# ============================================================================
# FORMULARIOS IMPLEMENTADOS
# ============================================================================

@register_form("lab_analysis_result")
def render_lab_analysis_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Análisis de Laboratorio (TTO-03).
    
    Captura: pH, Humedad, Sólidos, Observaciones
    """
    st.subheader("📊 Análisis de Laboratorio")
    st.markdown("*Registra los resultados del análisis de calidad del lodo*")
    
    with st.form(f"lab_form_{load_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            ph = st.number_input(
                "pH",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1,
                help="Nivel de acidez/alcalinidad"
            )
            
            humidity = st.number_input(
                "Humedad (%)",
                min_value=0.0,
                max_value=100.0,
                value=75.0,
                step=0.1,
                help="Porcentaje de contenido de agua"
            )
        
        with col2:
            solids = st.number_input(
                "Sólidos (%)",
                min_value=0.0,
                max_value=100.0,
                value=3.5,
                step=0.1,
                help="Porcentaje de sólidos totales"
            )
            
            temperature = st.number_input(
                "Temperatura (°C)",
                min_value=-20.0,
                max_value=100.0,
                value=20.0,
                step=0.5,
                help="Temperatura de la muestra"
            )
        
        notes = st.text_area(
            "Observaciones",
            placeholder="Cualquier nota relevante sobre la muestra...",
            height=100
        )
        
        submitted = st.form_submit_button(
            "💾 Guardar Análisis",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            return {
                "ph": ph,
                "humidity": humidity,
                "solids": solids,
                "temperature": temperature,
                "notes": notes,
                "timestamp": datetime.now().isoformat(),
                "technician_id": st.session_state.get("user_id", 1),
            }
    
    return None


@register_form("gate_entry_check")
def render_gate_entry_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Registro en Portería.
    
    Captura: Patente, Conductor, Hora de ingreso
    """
    st.subheader("🚧 Registro en Portería")
    st.markdown("*Registra el ingreso del vehículo a la planta*")
    
    with st.form(f"gate_form_{load_id}", clear_on_submit=False):
        vehicle_plate = st.text_input(
            "Patente del Vehículo",
            placeholder="AA-BB-12",
            help="Patente del camión que ingresa"
        )
        
        driver_name = st.text_input(
            "Nombre del Conductor",
            placeholder="Juan Pérez",
            help="Conductor que presenta en portería"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            has_documents = st.checkbox(
                "Documentación en regla",
                value=True,
                help="Licencia, permisos, guías"
            )
        
        with col2:
            has_ppe = st.checkbox(
                "EPP completo",
                value=True,
                help="Elementos de protección personal"
            )
        
        observations = st.text_area(
            "Observaciones",
            placeholder="Notas sobre el ingreso...",
            height=80
        )
        
        submitted = st.form_submit_button(
            "✅ Registrar Ingreso",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not vehicle_plate or not driver_name:
                st.error("⚠️ Patente y nombre del conductor son obligatorios")
                return None
            
            return {
                "timestamp": datetime.now().isoformat(),
                "vehicle_plate": vehicle_plate.upper(),
                "driver_name": driver_name,
                "has_documents": has_documents,
                "has_ppe": has_ppe,
                "observations": observations,
                "guard_id": st.session_state.get("user_id", 1),
            }
    
    return None


@register_form("entry_weight_ticket")
def render_entry_weight_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Pesaje de Entrada.
    
    Captura: Peso bruto, Número de ticket
    """
    st.subheader("⚖️ Pesaje de Entrada")
    st.markdown("*Registra el peso del vehículo cargado*")
    
    with st.form(f"weight_entry_{load_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_number = st.text_input(
                "Número de Ticket",
                placeholder="TKT-00123",
                help="Número del ticket de báscula"
            )
        
        with col2:
            gross_weight = st.number_input(
                "Peso Bruto (kg)",
                min_value=0,
                value=15000,
                step=100,
                help="Peso total del vehículo cargado"
            )
        
        notes = st.text_area(
            "Observaciones",
            placeholder="Notas sobre el pesaje...",
            height=60
        )
        
        submitted = st.form_submit_button(
            "💾 Guardar Pesaje",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not ticket_number:
                st.error("⚠️ Número de ticket es obligatorio")
                return None
            
            if gross_weight <= 0:
                st.error("⚠️ El peso debe ser mayor a 0")
                return None
            
            return {
                "ticket_number": ticket_number.upper(),
                "gross_weight": gross_weight,
                "timestamp": datetime.now().isoformat(),
                "operator_id": st.session_state.get("user_id", 1),
            }
    
    return None


@register_form("exit_weight_ticket")
def render_exit_weight_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Pesaje de Salida.
    
    Captura: Peso tara, Número de ticket
    """
    st.subheader("⚖️ Pesaje de Salida")
    st.markdown("*Registra el peso del vehículo vacío*")
    
    with st.form(f"weight_exit_{load_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_number = st.text_input(
                "Número de Ticket",
                placeholder="TKT-00124",
                help="Número del ticket de báscula de salida"
            )
        
        with col2:
            tare_weight = st.number_input(
                "Peso Tara (kg)",
                min_value=0,
                value=8000,
                step=100,
                help="Peso del vehículo vacío"
            )
        
        notes = st.text_area(
            "Observaciones",
            placeholder="Notas sobre el pesaje...",
            height=60
        )
        
        submitted = st.form_submit_button(
            "💾 Guardar Pesaje",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not ticket_number:
                st.error("⚠️ Número de ticket es obligatorio")
                return None
            
            if tare_weight <= 0:
                st.error("⚠️ El peso debe ser mayor a 0")
                return None
            
            return {
                "ticket_number": ticket_number.upper(),
                "tare_weight": tare_weight,
                "timestamp": datetime.now().isoformat(),
                "operator_id": st.session_state.get("user_id", 1),
            }
    
    return None


@register_form("driver_acceptance")
def render_driver_acceptance_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Aceptación de Viaje por Conductor.
    
    Captura: Confirmación del conductor
    """
    st.subheader("👍 Aceptar Viaje")
    st.markdown("*Confirma que estás listo para iniciar el viaje*")
    
    st.info("📋 Al aceptar, confirmas que:")
    st.markdown("""
    - Has revisado los detalles del viaje
    - El vehículo está en condiciones óptimas
    - Conoces la ruta y el destino
    """)
    
    with st.form(f"accept_form_{load_id}", clear_on_submit=False):
        vehicle_condition = st.selectbox(
            "Estado del Vehículo",
            options=["Óptimo", "Bueno", "Regular", "Requiere revisión"],
            help="Condición actual del vehículo"
        )
        
        comments = st.text_area(
            "Comentarios (opcional)",
            placeholder="Cualquier nota relevante...",
            height=80
        )
        
        confirm = st.checkbox(
            "Confirmo que estoy listo para iniciar el viaje",
            value=False
        )
        
        submitted = st.form_submit_button(
            "✅ Aceptar Viaje",
            use_container_width=True,
            type="primary",
            disabled=not confirm
        )
        
        if submitted and confirm:
            return {
                "timestamp": datetime.now().isoformat(),
                "driver_id": st.session_state.get("user_id", 1),
                "vehicle_condition": vehicle_condition,
                "comments": comments,
                "accepted": True,
            }
    
    return None


@register_form("pickup_confirmation")
def render_pickup_confirmation_form(load_id: int) -> Optional[Dict[str, Any]]:
    """
    Formulario de Confirmación de Carga Completada.
    
    Captura: Confirmación de que la carga en origen finalizó
    """
    st.subheader("📦 Confirmar Carga Completada")
    st.markdown("*Confirma que la carga en origen ha finalizado*")
    
    with st.form(f"pickup_form_{load_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            estimated_weight = st.number_input(
                "Peso Estimado (kg)",
                min_value=0,
                value=10000,
                step=100,
                help="Estimación visual del peso cargado"
            )
        
        with col2:
            container_sealed = st.checkbox(
                "Contenedor sellado",
                value=True,
                help="El contenedor está correctamente sellado"
            )
        
        loading_time_minutes = st.slider(
            "Tiempo de Carga (minutos)",
            min_value=5,
            max_value=120,
            value=30,
            step=5,
            help="Tiempo que tomó completar la carga"
        )
        
        observations = st.text_area(
            "Observaciones",
            placeholder="Notas sobre el proceso de carga...",
            height=80
        )
        
        submitted = st.form_submit_button(
            "✅ Confirmar Carga",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            return {
                "timestamp": datetime.now().isoformat(),
                "estimated_weight": estimated_weight,
                "container_sealed": container_sealed,
                "loading_time_minutes": loading_time_minutes,
                "observations": observations,
                "driver_id": st.session_state.get("user_id", 1),
            }
    
    return None


# ============================================================================
# UTILIDADES
# ============================================================================

def get_all_registered_forms() -> Dict[str, str]:
    """
    Retorna un diccionario con todos los formularios registrados.
    
    Útil para debugging y documentación.
    
    Returns:
        Dict mapeando verifier_key -> nombre de función
    """
    return {
        key: func.__name__
        for key, func in FORM_REGISTRY.items()
    }


def is_form_registered(verifier_key: str) -> bool:
    """Verifica si existe un formulario para un verificador"""
    return verifier_key in FORM_REGISTRY

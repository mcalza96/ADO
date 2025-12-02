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

FormRenderer = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]


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
# ADDITIONAL FORMS FOR TASK RESOLVER
# ============================================================================

@register_form("lab_check")
def render_lab_check_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Alias para lab_analysis_result - compatibilidad con TaskResolver
    """
    load = context.get('load')
    return render_lab_analysis_form(load.id if load else 0)


@register_form("gate_check")
def render_gate_check_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Alias para gate_entry_check - compatibilidad con TaskResolver
    """
    load = context.get('load')
    return render_gate_entry_form(load.id if load else 0)


@register_form("pickup_check")
def render_pickup_check_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Alias para pickup_confirmation - compatibilidad con TaskResolver
    """
    load = context.get('load')
    return render_pickup_confirmation_form(load.id if load else 0)


@register_form("weight_check")
def render_weight_check_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Formulario inteligente de pesaje - determina si es entrada o salida
    basado en los atributos existentes de la carga.
    """
    load = context.get('load')
    if not load:
        st.error("❌ No se proporcionó información de la carga")
        return None
    
    # Determinar si es entrada o salida basado en atributos
    has_entry_weight = load.attributes and 'entry_weight_ticket' in load.attributes
    
    if has_entry_weight:
        # Ya tiene peso de entrada, entonces es salida
        return render_exit_weight_form(load.id)
    else:
        # No tiene peso de entrada, entonces es entrada
        return render_entry_weight_form(load.id)


@register_form("geofence_check")
def render_geofence_check_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Formulario de Confirmación de Geofence (Llegada a Origen).
    
    Captura: Confirmación automática/manual de llegada a coordenadas
    """
    load = context.get('load')
    if not load:
        return None
    
    st.subheader("📍 Confirmar Llegada a Origen")
    st.markdown("*Confirma que has llegado al punto de origen*")
    
    with st.form(f"geofence_form_{load.id}", clear_on_submit=False):
        st.info("🗺️ Sistema de geolocalización detectó tu posición")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input(
                "Latitud",
                value=-33.4489,
                format="%.6f",
                help="Coordenada de latitud actual"
            )
        
        with col2:
            longitude = st.number_input(
                "Longitud", 
                value=-70.6693,
                format="%.6f",
                help="Coordenada de longitud actual"
            )
        
        arrival_time = st.time_input(
            "Hora de Llegada",
            value=datetime.now().time(),
            help="Hora de llegada al origen"
        )
        
        observations = st.text_area(
            "Observaciones",
            placeholder="Condiciones del sitio, acceso, etc...",
            height=80
        )
        
        submitted = st.form_submit_button(
            "✅ Confirmar Llegada",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            return {
                "geofence_confirmation": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "arrival_time": arrival_time.isoformat(),
                    "timestamp": datetime.now().isoformat(),
                    "observations": observations,
                    "driver_id": st.session_state.get("user_id", 1),
                }
            }
    
    return None


@register_form("ticket_upload")
def render_ticket_upload_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Formulario de Subida de Ticket de Pesaje Final.
    
    Captura: Archivo adjunto y metadatos del ticket
    """
    load = context.get('load')
    if not load:
        return None
    
    st.subheader("📄 Subir Ticket de Pesaje Final")
    st.markdown("*Adjunta el ticket de báscula final*")
    
    with st.form(f"ticket_form_{load.id}", clear_on_submit=False):
        ticket_file = st.file_uploader(
            "Archivo del Ticket",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Fotografía o PDF del ticket de pesaje"
        )
        
        ticket_number = st.text_input(
            "Número de Ticket",
            placeholder="TKT-FINAL-00123",
            help="Número del ticket final"
        )
        
        final_weight = st.number_input(
            "Peso Final Registrado (kg)",
            min_value=0,
            value=0,
            step=100,
            help="Peso neto final según ticket"
        )
        
        notes = st.text_area(
            "Notas Adicionales",
            placeholder="Observaciones sobre el ticket final...",
            height=60
        )
        
        submitted = st.form_submit_button(
            "💾 Guardar Ticket",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if not ticket_number:
                st.error("⚠️ Número de ticket es obligatorio")
                return None
            
            result = {
                "weight_ticket_final": {
                    "ticket_number": ticket_number.upper(),
                    "final_weight": final_weight,
                    "notes": notes,
                    "timestamp": datetime.now().isoformat(),
                    "uploaded_by": st.session_state.get("user_id", 1),
                }
            }
            
            # Si hay archivo, guardar referencia (en producción, subir a S3/Storage)
            if ticket_file:
                result["weight_ticket_final"]["file_name"] = ticket_file.name
                result["weight_ticket_final"]["file_size"] = ticket_file.size
                # TODO: Implementar upload a storage cloud
                st.success(f"✅ Archivo '{ticket_file.name}' listo para subir")
            
            return result
    
    return None


@register_form("daily_log")
def render_daily_log_form(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Formulario de Parte Diario de Maquinaria.
    
    Captura: Horómetro, combustible, actividad, observaciones
    """
    machine_id = context.get('machine_id', 1)
    
    st.subheader("🚜 Parte Diario de Maquinaria")
    st.markdown(f"*Máquina #{machine_id}*")
    
    with st.form(f"daily_log_{machine_id}", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            start_hourmeter = st.number_input(
                "Horómetro Inicial",
                min_value=0.0,
                value=1000.0,
                step=0.1,
                help="Lectura del horómetro al inicio del día"
            )
        
        with col2:
            end_hourmeter = st.number_input(
                "Horómetro Final",
                min_value=start_hourmeter,
                value=start_hourmeter + 8.0,
                step=0.1,
                help="Lectura del horómetro al final del día"
            )
        
        fuel_consumed = st.number_input(
            "Combustible Consumido (litros)",
            min_value=0.0,
            value=50.0,
            step=5.0,
            help="Litros de combustible consumidos"
        )
        
        activity_type = st.selectbox(
            "Tipo de Actividad",
            options=["Esparcido", "Incorporación", "Transporte Interno", "Mantenimiento", "Stand-by"],
            help="Principal actividad realizada"
        )
        
        area_worked = st.number_input(
            "Área Trabajada (hectáreas)",
            min_value=0.0,
            value=5.0,
            step=0.5,
            help="Hectáreas trabajadas en el día"
        )
        
        operational_status = st.selectbox(
            "Estado Operacional",
            options=["Operativo", "Requiere Mantención Menor", "Requiere Mantención Mayor", "Fuera de Servicio"],
            help="Estado de la máquina al final del día"
        )
        
        observations = st.text_area(
            "Observaciones",
            placeholder="Novedades, problemas detectados, condiciones del terreno...",
            height=100
        )
        
        submitted = st.form_submit_button(
            "💾 Guardar Parte Diario",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            hours_worked = end_hourmeter - start_hourmeter
            
            if hours_worked <= 0:
                st.error("⚠️ El horómetro final debe ser mayor al inicial")
                return None
            
            return {
                "machine_log": {
                    "machine_id": machine_id,
                    "date": datetime.now().date().isoformat(),
                    "start_hourmeter": start_hourmeter,
                    "end_hourmeter": end_hourmeter,
                    "hours_worked": hours_worked,
                    "fuel_consumed": fuel_consumed,
                    "activity_type": activity_type,
                    "area_worked": area_worked,
                    "operational_status": operational_status,
                    "observations": observations,
                    "operator_id": st.session_state.get("user_id", 1),
                    "timestamp": datetime.now().isoformat(),
                }
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

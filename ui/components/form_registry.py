import streamlit as st
from typing import Dict, Any, Callable

# ============================================================================
# FORM RENDERERS
# ============================================================================

def render_lab_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario para TTO-03: Análisis de Laboratorio"""
    st.subheader("🧪 Análisis de Laboratorio")
    
    with st.form("lab_form"):
        col1, col2 = st.columns(2)
        ph = col1.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
        humidity = col2.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1)
        
        temp = st.number_input("Temperatura (°C)", value=20.0)
        smell = st.selectbox("Olor", ["Normal", "Fuerte", "Pútrido"])
        
        submitted = st.form_submit_button("Guardar Análisis")
        
        if submitted:
            return {
                "lab_analysis_ok": True, # Flag para validador
                "lab_analysis_result": {
                    "ph": ph,
                    "humidity": humidity,
                    "temperature": temp,
                    "smell": smell
                }
            }
    return None

def render_gate_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario para Portería"""
    st.subheader("🚧 Registro de Portería")
    
    with st.form("gate_form"):
        plate = st.text_input("Patente Confirmada")
        driver_rut = st.text_input("RUT Conductor")
        
        submitted = st.form_submit_button("Registrar Ingreso")
        
        if submitted:
            return {
                "gate_entry": {
                    "confirmed_plate": plate,
                    "driver_rut": driver_rut,
                    "timestamp": "now" # Backend should fix this
                }
            }
    return None

def render_pickup_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario para Confirmación de Carga"""
    st.subheader("📦 Confirmación de Carga")
    
    with st.form("pickup_form"):
        st.info("Confirme que la carga ha sido estibada y asegurada correctamente.")
        check_seals = st.checkbox("Sellos verificados")
        check_docs = st.checkbox("Documentación entregada")
        
        submitted = st.form_submit_button("Confirmar Salida")
        
        if submitted and check_seals and check_docs:
            return {
                "manual_pickup_confirmation": True,
                "pickup_checklist": {
                    "seals": True,
                    "docs": True
                }
            }
    return None

def render_daily_log(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario para Parte Diario de Maquinaria"""
    st.subheader("🚜 Parte Diario de Maquinaria")
    machine_id = payload.get('machine_id')
    st.caption(f"Máquina ID: {machine_id}")
    
    with st.form("log_form"):
        col1, col2 = st.columns(2)
        start_hm = col1.number_input("Horómetro Inicial", min_value=0.0, step=0.1)
        end_hm = col2.number_input("Horómetro Final", min_value=0.0, step=0.1)
        
        st.markdown("### Actividades")
        activity = st.text_input("Descripción Actividad")
        site_id = st.number_input("ID Sitio", value=1, step=1)
        
        submitted = st.form_submit_button("Guardar Parte Diario")
        
        if submitted:
            if end_hm <= start_hm:
                st.error("El horómetro final debe ser mayor al inicial")
                return None
                
            return {
                "machine_log": {
                    "machine_id": machine_id,
                    "operator_id": 1, # Mock
                    "site_id": site_id,
                    "start_hourmeter": start_hm,
                    "end_hourmeter": end_hm,
                    "activities": [{"task": activity}]
                }
            }
    return None

def render_weight_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario para Pesaje (Entrada o Salida)"""
    st.subheader("⚖️ Registro de Pesaje")
    
    with st.form("weight_form"):
        st.info("Complete los datos del pesaje. El peso neto se calcula automáticamente.")
        
        col1, col2 = st.columns(2)
        gross_weight = col1.number_input("Peso Bruto (kg)", min_value=0.0, step=10.0, help="Peso total del vehículo cargado")
        tare_weight = col2.number_input("Tara (kg)", min_value=0.0, step=10.0, help="Peso del vehículo vacío")
        
        ticket_number = st.text_input("N° Ticket Balanza", help="Número del ticket de la báscula")
        
        # Cálculo automático de peso neto
        net_weight = gross_weight - tare_weight
        st.metric("Peso Neto Calculado", f"{net_weight:.2f} kg", 
                 delta=f"Bruto: {gross_weight} - Tara: {tare_weight}")
        
        submitted = st.form_submit_button("Guardar Pesaje")
        
        if submitted:
            # Validaciones
            if net_weight <= 0:
                st.error("❌ Error: El peso neto debe ser mayor a cero. Verifique peso bruto y tara.")
                return None
            
            if not ticket_number or ticket_number.strip() == "":
                st.error("❌ Error: Debe ingresar el número de ticket de balanza.")
                return None
            
            return {
                "weight_entry": {
                    "gross_weight": gross_weight,
                    "tare": tare_weight,
                    "net_weight": net_weight,
                    "ticket_number": ticket_number.strip()
                }
            }
    return None

def render_geofence_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario manual de confirmación si geocerca automática falla"""
    st.subheader("📍 Confirmación de Ubicación")
    
    st.warning("⚠️ La verificación automática de geocerca no está disponible. Por favor, confirme manualmente.")
    
    with st.form("geofence_form"):
        st.markdown("### Confirmación Manual")
        st.caption("Use esta opción solo si está físicamente en el lugar correcto.")
        
        # Coordenadas GPS opcionales
        with st.expander("📌 Coordenadas GPS (Opcional)"):
            col1, col2 = st.columns(2)
            latitude = col1.number_input("Latitud", value=0.0, format="%.6f", 
                                        help="Ej: -33.448890")
            longitude = col2.number_input("Longitud", value=0.0, format="%.6f", 
                                         help="Ej: -70.669265")
        
        # Foto de evidencia (opcional para MVP)
        photo_evidence = st.file_uploader("📸 Foto de Evidencia (Opcional)", 
                                         type=['jpg', 'jpeg', 'png'],
                                         help="Suba una foto del lugar para verificación posterior")
        
        # Confirmación explícita
        confirm = st.checkbox("✅ Confirmo que estoy en el lugar correcto", value=False)
        
        submitted = st.form_submit_button("Confirmar Ubicación")
        
        if submitted:
            if not confirm:
                st.error("❌ Debe confirmar que está en el lugar correcto antes de continuar.")
                return None
            
            result = {
                "geofence_confirmation_manual": True,
                "confirmation_metadata": {
                    "method": "manual"
                }
            }
            
            # Agregar coordenadas si se proporcionaron
            if latitude != 0.0 or longitude != 0.0:
                result["confirmation_metadata"]["coordinates"] = {
                    "lat": latitude,
                    "lon": longitude
                }
            
            # Guardar foto si se subió (mock para MVP)
            if photo_evidence:
                result["confirmation_metadata"]["photo_uploaded"] = True
                result["confirmation_metadata"]["photo_name"] = photo_evidence.name
                # TODO: En producción, guardar en carpeta uploads/ o S3
                st.info(f"📸 Foto guardada: {photo_evidence.name}")
            
            return result
    return None

def render_ticket_upload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Formulario de subida de documentos (tickets, guías, etc.)"""
    st.subheader("📄 Subir Documentación")
    
    with st.form("ticket_upload_form"):
        st.info("Suba los documentos requeridos para completar el proceso.")
        
        # Tipo de documento
        doc_type = st.selectbox(
            "Tipo de Documento",
            ["Ticket Balanza", "Guía de Despacho", "Manifiesto de Residuos", "Otro"]
        )
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Seleccionar Archivo",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Formatos aceptados: PDF, JPG, PNG"
        )
        
        # Observaciones opcionales
        notes = st.text_area("Observaciones (Opcional)", 
                            placeholder="Ingrese cualquier observación relevante...")
        
        submitted = st.form_submit_button("Subir Documento")
        
        if submitted:
            if not uploaded_file:
                st.error("❌ Error: Debe seleccionar un archivo antes de continuar.")
                return None
            
            # Mock: En producción, guardar en carpeta uploads/ o S3
            file_name = f"{doc_type.replace(' ', '_')}_{uploaded_file.name}"
            
            # TODO: Implementar guardado real
            # import os
            # uploads_dir = "uploads/"
            # os.makedirs(uploads_dir, exist_ok=True)
            # file_path = os.path.join(uploads_dir, file_name)
            # with open(file_path, "wb") as f:
            #     f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ Documento '{file_name}' guardado exitosamente (mock)")
            
            return {
                "weight_ticket_final": True,  # Flag para validador
                "document_uploaded": {
                    "type": doc_type,
                    "filename": file_name,
                    "original_name": uploaded_file.name,
                    "notes": notes.strip() if notes else None
                }
            }
    return None

# ============================================================================
# REGISTRY
# ============================================================================

FORM_REGISTRY: Dict[str, Callable] = {
    "lab_check": render_lab_check,
    "gate_check": render_gate_check,
    "pickup_check": render_pickup_check,
    "daily_log": render_daily_log,
    "weight_check": render_weight_check,
    "geofence_check": render_geofence_check,
    "ticket_upload": render_ticket_upload
}


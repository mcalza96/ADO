import streamlit as st
from datetime import datetime, timedelta
from ui.styles import apply_industrial_style
from domain.logistics.entities.pickup_request import PickupRequestStatus
from domain.logistics.entities.container_filling_record import ContainerFillingStatus

def ds4_monitoring_view(plant_id: int, container_service, logistics_service, pickup_request_service, container_tracking_service=None):
    """DS4 Monitoring view - Proceso de estabilización alcalina y solicitud de retiros."""
        
    st.subheader("🧪 Proceso DS4 (Salida)")
    
    tab_llenado, tab_solicitar, tab_historial = st.tabs([
        "📦 Llenado de Contenedores",
        "📝 Solicitar Retiro", 
        "📋 Historial de Solicitudes"
    ])
    
    with tab_llenado:
        _render_container_filling_tab(plant_id, container_tracking_service)
    
    with tab_solicitar:
        _render_request_form(plant_id, pickup_request_service)
    
    with tab_historial:
        _render_request_history(plant_id, pickup_request_service)


def _render_request_form(plant_id: int, pickup_request_service):
    """Renderiza el formulario de solicitud de retiro."""
    st.markdown("### Solicitar Camión de Retiro")
    st.info(
        "🚛 **Retiros AMPLIROLL con 2 contenedores**\n\n"
        "Cada solicitud genera cargas para camiones AMPLIROLL que retirarán "
        "2 contenedores cada uno. Los contenedores específicos se asignarán "
        "al momento del despacho."
    )
    
    with st.form("request_truck"):
        col1, col2 = st.columns(2)
        
        with col1:
            req_date = st.date_input(
                "Fecha Solicitada", 
                datetime.today(),
                min_value=datetime.today().date(),
                help="Fecha en que se requiere el retiro"
            )
        
        with col2:
            qty = st.number_input(
                "Cantidad de Camiones", 
                min_value=1, 
                max_value=10, 
                value=1,
                help="Cada camión retira 2 contenedores"
            )
        
        notes = st.text_area(
            "Observaciones (opcional)",
            placeholder="Ej: Priorizar contenedores con más tiempo de estabilización",
            height=80
        )
        
        # Info resumen
        st.markdown(f"""
        **Resumen de la solicitud:**
        - 🚛 **{qty}** camión(es) AMPLIROLL
        - 📦 **{qty * 2}** contenedores totales (2 por camión)
        """)
        
        if st.form_submit_button("🚛 Solicitar Retiro", type="primary"):
            try:
                request = pickup_request_service.create_treatment_plant_request(
                    treatment_plant_id=plant_id,
                    requested_date=req_date,
                    load_quantity=qty,
                    notes=notes if notes.strip() else None
                )
                st.success(f"✅ Solicitud #{request.id} creada exitosamente. Se generaron {qty} cargas pendientes de asignar.")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ Error: {e}")
            except Exception as e:
                st.error(f"❌ Error al crear solicitud: {e}")


def _render_request_history(plant_id: int, pickup_request_service):
    """Renderiza el historial de solicitudes de la planta."""
    st.markdown("### Historial de Solicitudes")
    
    # Obtener solicitudes de esta planta
    requests = pickup_request_service.get_by_treatment_plant(plant_id, include_completed=True)
    
    if not requests:
        st.info("📭 No hay solicitudes de retiro registradas para esta planta.")
        return
    
    # Separar por estado
    pending = [r for r in requests if r.status in [
        PickupRequestStatus.PENDING.value, 
        PickupRequestStatus.PARTIALLY_SCHEDULED.value
    ]]
    in_progress = [r for r in requests if r.status in [
        PickupRequestStatus.FULLY_SCHEDULED.value,
        PickupRequestStatus.IN_PROGRESS.value
    ]]
    completed = [r for r in requests if r.status == PickupRequestStatus.COMPLETED.value]
    
    # Métricas resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏳ Pendientes", len(pending))
    with col2:
        st.metric("🚛 En Proceso", len(in_progress))
    with col3:
        st.metric("✅ Completadas", len(completed))
    
    st.divider()
    
    # Mostrar solicitudes pendientes primero
    if pending:
        st.markdown("#### ⏳ Solicitudes Pendientes")
        for req in pending:
            _render_request_card(req, pickup_request_service, show_cancel=True)
    
    # Solicitudes en proceso
    if in_progress:
        st.markdown("#### 🚛 En Proceso")
        for req in in_progress:
            _render_request_card(req, pickup_request_service)
    
    # Mostrar completadas en un expander
    if completed:
        with st.expander(f"✅ Completadas ({len(completed)})"):
            for req in completed:
                _render_request_card(req, pickup_request_service, compact=True)


def _render_request_card(request, pickup_request_service, show_cancel: bool = False, compact: bool = False):
    """Renderiza una tarjeta de solicitud."""
    status_icons = {
        PickupRequestStatus.PENDING.value: "⏳",
        PickupRequestStatus.PARTIALLY_SCHEDULED.value: "📅",
        PickupRequestStatus.FULLY_SCHEDULED.value: "✔️",
        PickupRequestStatus.IN_PROGRESS.value: "🚛",
        PickupRequestStatus.COMPLETED.value: "✅",
        PickupRequestStatus.CANCELLED.value: "❌"
    }
    
    status_icon = status_icons.get(request.status, "❓")
    scheduled = request.scheduled_count or 0
    
    if compact:
        st.markdown(
            f"**#{request.id}** | {request.requested_date} | "
            f"{request.load_quantity} camiones | {status_icon} {request.status}"
        )
    else:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**Solicitud #{request.id}**")
                st.caption(f"📅 Fecha: {request.requested_date}")
                if request.notes:
                    st.caption(f"📝 {request.notes}")
            
            with col2:
                st.markdown(f"🚛 **{request.load_quantity}** camiones")
                st.caption(f"📦 {request.load_quantity * 2} contenedores")
                st.caption(f"Programadas: {scheduled}/{request.load_quantity}")
            
            with col3:
                st.markdown(f"{status_icon} **{request.status}**")
                if show_cancel and request.status == PickupRequestStatus.PENDING.value:
                    if st.button("❌ Cancelar", key=f"cancel_{request.id}", type="secondary"):
                        if pickup_request_service.cancel_request(request.id):
                            st.success("Solicitud cancelada")
                            st.rerun()
            
            st.divider()


# =============================================================================
# Container Filling Tab
# =============================================================================

def _render_container_filling_tab(plant_id: int, container_tracking_service):
    """Renderiza la pestaña de llenado de contenedores con pH y humedad."""
    
    if container_tracking_service is None:
        st.warning("⚠️ El servicio de seguimiento de contenedores no está disponible.")
        return
    
    st.markdown("### 📦 Registro de Llenado de Contenedores")
    st.info(
        "🧪 **Proceso de Estabilización Alcalina (Encalado)**\n\n"
        "Registre aquí cuando un contenedor termine de llenarse con lodo encalado. "
        "Debe ingresar la humedad y pH inicial (0h). El sistema bloqueará el ingreso "
        "de pH a 2h y 24h hasta que transcurra el tiempo requerido. "
        "El contenedor puede despacharse mientras se mantiene una muestra para las mediciones."
    )
    
    # Sección 1: Nuevo registro de llenado
    _render_new_filling_form(plant_id, container_tracking_service)
    
    st.divider()
    
    # Sección 2: Contenedores con pH pendiente
    _render_pending_ph_section(plant_id, container_tracking_service)
    
    st.divider()
    
    # Sección 3: Historial de contenedores
    _render_container_history(plant_id, container_tracking_service)


def _render_new_filling_form(plant_id: int, container_tracking_service):
    """Formulario para registrar un nuevo llenado de contenedor."""
    st.markdown("#### ➕ Nuevo Registro de Llenado")
    
    # Obtener contenedores disponibles
    available_containers = container_tracking_service.get_available_containers(plant_id)
    
    if not available_containers:
        st.warning("⚠️ No hay contenedores disponibles. Todos están en uso o en mantenimiento.")
        return
    
    with st.form("new_filling_record", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selector de contenedor
            container_options = {c.id: f"{c.code} ({c.capacity_m3}m³)" for c in available_containers}
            selected_container_id = st.selectbox(
                "Contenedor *",
                options=list(container_options.keys()),
                format_func=lambda x: container_options[x],
                help="Seleccione el contenedor que terminó de llenarse"
            )
            
            # Hora de fin de llenado
            fill_date = st.date_input(
                "Fecha de llenado *",
                value=datetime.today(),
                max_value=datetime.today().date()
            )
            fill_time = st.time_input(
                "Hora de fin de llenado *",
                value=datetime.now().time()
            )
        
        with col2:
            # Mediciones iniciales
            humidity = st.number_input(
                "Humedad (%) *",
                min_value=0.0,
                max_value=100.0,
                value=75.0,
                step=0.1,
                help="Porcentaje de humedad del lodo encalado"
            )
            
            ph_0h = st.number_input(
                "pH Inicial (0h) *",
                min_value=0.0,
                max_value=14.0,
                value=12.0,
                step=0.1,
                help="pH medido al momento de terminar el llenado"
            )
        
        notes = st.text_area(
            "Observaciones (opcional)",
            placeholder="Ej: Lodo con alta viscosidad, requirió más cal",
            height=80
        )
        
        submitted = st.form_submit_button("📝 Registrar Llenado", type="primary")
        
        if submitted:
            try:
                fill_end_time = datetime.combine(fill_date, fill_time)
                
                record = container_tracking_service.create_filling_record(
                    container_id=selected_container_id,
                    treatment_plant_id=plant_id,
                    fill_end_time=fill_end_time,
                    humidity=humidity,
                    ph_0h=ph_0h,
                    notes=notes if notes.strip() else None,
                    created_by=st.session_state.get('username', 'unknown')
                )
                
                st.success(
                    f"✅ Registro creado exitosamente.\n\n"
                    f"**Contenedor:** {record.container_code}\n"
                    f"**pH₀:** {ph_0h} | **Humedad:** {humidity}%\n\n"
                    f"⏰ pH a 2h disponible en: {record.time_until_ph_2h:.1f} horas"
                )
                st.rerun()
            except ValueError as e:
                st.error(f"❌ Error: {e}")
            except Exception as e:
                st.error(f"❌ Error al crear registro: {e}")


def _render_pending_ph_section(plant_id: int, container_tracking_service):
    """Muestra contenedores con mediciones de pH pendientes."""
    st.markdown("#### 🕐 Mediciones de pH Pendientes")
    
    # Obtener TODOS los registros activos (no despachados)
    all_records = container_tracking_service.get_active_records_by_plant(plant_id)
    active_records = [r for r in all_records 
                      if r.status != ContainerFillingStatus.DISPATCHED.value]
    
    if not active_records:
        st.info("✅ No hay contenedores con mediciones de pH pendientes.")
        return
    
    # Mostrar cada contenedor con su estado de mediciones
    for record in active_records:
        with st.container():
            # Header del contenedor
            col_header, col_status = st.columns([3, 1])
            with col_header:
                st.markdown(f"**📦 {record.container_code}**")
                st.caption(f"Llenado: {record.fill_end_time.strftime('%d/%m %H:%M')} | Humedad: {record.humidity}%")
            with col_status:
                st.markdown(f"*{record.display_status}*")
            
            # Mostrar mediciones en columnas
            col1, col2, col3 = st.columns(3)
            
            # pH 0h (siempre registrado)
            with col1:
                st.metric("pH₀ (inicial)", f"{record.ph_0h:.1f}")
            
            # pH 2h
            with col2:
                if record.ph_2h is not None:
                    st.metric("pH₂ (2 horas)", f"{record.ph_2h:.1f}")
                elif record.can_record_ph_2h:
                    # Listo para medir
                    _render_ph_input_inline(record, 'ph_2h', container_tracking_service)
                else:
                    # Esperando tiempo
                    time_remaining = record.time_until_ph_2h
                    if time_remaining:
                        st.metric("pH₂ (2 horas)", f"⏳ {time_remaining:.1f}h")
                    else:
                        st.metric("pH₂ (2 horas)", "—")
            
            # pH 24h
            with col3:
                if record.ph_24h is not None:
                    st.metric("pH₂₄ (24 horas)", f"{record.ph_24h:.1f}")
                elif record.can_record_ph_24h:
                    # Listo para medir
                    _render_ph_input_inline(record, 'ph_24h', container_tracking_service)
                else:
                    # Esperando tiempo
                    time_remaining = record.time_until_ph_24h
                    if time_remaining:
                        st.metric("pH₂₄ (24 horas)", f"⏳ {time_remaining:.1f}h")
                    else:
                        st.metric("pH₂₄ (24 horas)", "—")
            
            st.divider()


def _render_ph_input_inline(record, ph_type: str, container_tracking_service):
    """Renderiza input de pH inline con botón."""
    label = "pH₂" if ph_type == 'ph_2h' else "pH₂₄"
    key_suffix = f"{record.id}_{ph_type}"
    
    ph_value = st.number_input(
        f"{label} ✅",
        min_value=0.0,
        max_value=14.0,
        value=12.0,
        step=0.1,
        key=f"ph_input_{key_suffix}",
        label_visibility="collapsed"
    )
    
    if st.button("💾", key=f"save_{key_suffix}", help=f"Guardar {label}"):
        try:
            if ph_type == 'ph_2h':
                container_tracking_service.update_ph_2h(record.id, ph_value)
            else:
                container_tracking_service.update_ph_24h(record.id, ph_value)
            st.success(f"✓ {label} guardado")
            st.rerun()
        except ValueError as e:
            st.error(str(e))


def _render_container_history(plant_id: int, container_tracking_service):
    """Muestra el historial de contenedores llenados."""
    st.markdown("#### 📋 Historial de Contenedores")
    
    records = container_tracking_service.get_active_records_by_plant(plant_id)
    
    if not records:
        st.info("📭 No hay registros de llenado para esta planta.")
        return
    
    # Separar por estado (soportar PENDING_PH y legacy FILLING)
    pending_ph = [r for r in records if r.status in (
        ContainerFillingStatus.PENDING_PH.value, 
        ContainerFillingStatus.FILLING.value  # Legacy
    )]
    ready = [r for r in records if r.status == ContainerFillingStatus.READY_FOR_DISPATCH.value]
    dispatched = [r for r in records if r.status == ContainerFillingStatus.DISPATCHED.value]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🧪 Pendiente pH", len(pending_ph))
    with col2:
        st.metric("✅ Listos p/ Despacho", len(ready))
    with col3:
        st.metric("🚚 Despachados", len(dispatched))
    
    # Tabla de registros
    if records:
        import pandas as pd
        
        data = []
        for r in records:
            data.append({
                'Contenedor': r.container_code or f"ID:{r.container_id}",
                'Fin Llenado': r.fill_end_time.strftime('%d/%m %H:%M') if r.fill_end_time else '-',
                'Humedad': f"{r.humidity:.1f}%" if r.humidity else '-',
                'pH₀': f"{r.ph_0h:.1f}" if r.ph_0h else '-',
                'pH₂': f"{r.ph_2h:.1f}" if r.ph_2h else '⏳',
                'pH₂₄': f"{r.ph_24h:.1f}" if r.ph_24h else '⏳',
                'Estado': r.display_status
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)

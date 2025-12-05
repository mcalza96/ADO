"""
Vista de Solicitud de Retiros para Clientes.

Permite a los clientes crear solicitudes de retiro agrupadas y ver su seguimiento.
"""
import streamlit as st
from datetime import date, datetime
from domain.logistics.entities.vehicle import VehicleType
from ui.presenters.status_presenter import StatusPresenter


def requests_page(container):
    """
    Página de solicitud de retiros para clientes.
    
    Args:
        container: SimpleNamespace con todos los servicios inyectados
    
    Nuevo flujo:
    - Cliente selecciona planta y tipo de vehículo
    - Especifica cantidad de retiros y contenedores (si AMPLIROLL)
    - Sistema genera cargas agrupadas en un PickupRequest
    """
    # Extraer servicios del container
    client_service = container.client_service
    facility_service = container.facility_service
    pickup_service = container.pickup_request_service
    logistics_service = container.logistics_service
    
    st.title("📝 Solicitud de Retiros")
    st.markdown("Ingrese las solicitudes de retiro para sus plantas.")
    
    # 1. Select Client (Simulating User Context - en producción vendría de la sesión)
    clients = client_service.get_all()
    if not clients:
        st.error("No hay clientes configurados.")
        return
        
    c_opts = {c.name: c.id for c in clients}
    sel_client = st.selectbox("🏢 Cliente (Generador)", list(c_opts.keys()))
    client_id = c_opts[sel_client]
    
    # Tabs para separar creación y seguimiento
    tab_nueva, tab_seguimiento = st.tabs(["➕ Nueva Solicitud", "📋 Mis Solicitudes"])
    
    with tab_nueva:
        _render_new_request_form(client_id, facility_service, pickup_service)
    
    with tab_seguimiento:
        _render_requests_tracking(client_id, pickup_service, logistics_service)


def _render_new_request_form(client_id: int, facility_service, pickup_service):
    """Renderiza el formulario de nueva solicitud de retiro."""
    
    # 2. Select Facility (plantas del cliente)
    facilities = facility_service.get_by_client(client_id)
    if not facilities:
        st.warning("Este cliente no tiene plantas registradas. Configure las plantas en Configuración > Empresas.")
        return
    
    f_opts = {f.name: f for f in facilities}
    sel_facility_name = st.selectbox("🏭 Planta de Origen", list(f_opts.keys()))
    facility = f_opts[sel_facility_name]
    
    # 3. Determinar tipos de vehículos permitidos
    allowed_types = _get_allowed_vehicle_types(facility)
    
    if not allowed_types:
        st.warning("Esta planta no tiene tipos de vehículos configurados. Configure los tipos permitidos en la planta.")
        return
    
    # 4. Detalles de la solicitud (fuera del form para actualización dinámica)
    st.subheader("📋 Detalles de la Solicitud")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Fecha solicitada
        req_date = st.date_input(
            "📅 Fecha Solicitada de Retiro",
            value=date.today(),
            min_value=date.today(),
            help="Fecha en que desea que se realicen los retiros"
        )
        
        # Tipo de vehículo
        type_options = [(t.value, t.display_name) for t in allowed_types]
        vehicle_type = st.selectbox(
            "🚛 Tipo de Vehículo",
            options=[v for v, _ in type_options],
            format_func=lambda x: dict(type_options).get(x, x),
            help="Seleccione el tipo de vehículo para los retiros"
        )
    
    with col2:
        # Cantidad de retiros
        num_loads = st.number_input(
            "📦 Cantidad de Retiros",
            min_value=1,
            max_value=50,
            value=1,
            help="Número de camiones/viajes que necesita"
        )
        
        # Contenedores por carga (solo AMPLIROLL)
        if vehicle_type == VehicleType.AMPLIROLL.value:
            containers_per_load = st.number_input(
                "🗑️ Contenedores por Carga",
                min_value=1,
                max_value=2,
                value=1,
                help="Cantidad de contenedores que lleva cada camión (máximo 2)"
            )
        else:
            containers_per_load = None
            st.info("ℹ️ Los vehículos BATEA realizan carga directa sin contenedores.")
    
    # Observaciones
    notes = st.text_area(
        "📝 Observaciones",
        placeholder="Indicaciones especiales, horarios preferidos, etc.",
        help="Información adicional para el transportista"
    )
    
    # Resumen dinámico (se actualiza inmediatamente)
    st.divider()
    st.write("**Resumen de la Solicitud:**")
    
    total_containers = num_loads * (containers_per_load or 0) if vehicle_type == VehicleType.AMPLIROLL.value else 0
    
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("Retiros", num_loads)
    with summary_cols[1]:
        st.metric("Tipo", vehicle_type)
    with summary_cols[2]:
        if vehicle_type == VehicleType.AMPLIROLL.value:
            st.metric("Contenedores Total", total_containers)
        else:
            st.metric("Tipo Carga", "Directa")
    with summary_cols[3]:
        st.metric("Fecha", req_date.strftime("%d/%m/%Y"))
    
    # Formulario solo para el botón de envío
    with st.form("pickup_request_form"):
        # Botón de envío
        submitted = st.form_submit_button("🚀 Enviar Solicitud", width='stretch', type="primary")
        
        if submitted:
            try:
                pickup_request = pickup_service.create_pickup_request(
                    client_id=client_id,
                    facility_id=facility.id,
                    requested_date=req_date,
                    vehicle_type=vehicle_type,
                    load_quantity=num_loads,
                    containers_per_load=containers_per_load,
                    notes=notes if notes else None
                )
                
                st.success(f"""
                ✅ **Solicitud #{pickup_request.id} creada exitosamente**
                
                - {num_loads} retiros programados para el {req_date.strftime('%d/%m/%Y')}
                - Tipo de vehículo: {vehicle_type}
                {f'- Total contenedores: {total_containers}' if total_containers else ''}
                
                El equipo de planificación asignará los recursos necesarios.
                """)
                st.balloons()
                
            except ValueError as e:
                st.error(f"❌ Error de validación: {e}")
            except Exception as e:
                st.error(f"❌ Error al crear solicitud: {e}")


def _render_requests_tracking(client_id: int, pickup_service, logistics_service):
    """Renderiza el seguimiento de solicitudes del cliente."""
    
    st.subheader("📊 Estado de mis Solicitudes")
    
    # Obtener solicitudes del cliente
    requests = pickup_service.get_by_client(client_id, include_completed=True)
    
    if not requests:
        st.info("No tiene solicitudes registradas aún.")
        return
    
    # Filtros
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        show_completed = st.checkbox("Mostrar completadas", value=False)
    
    if not show_completed:
        requests = [r for r in requests if r.status not in ['COMPLETED', 'CANCELLED']]
    
    if not requests:
        st.info("No hay solicitudes activas. Active 'Mostrar completadas' para ver el historial.")
        return
    
    # Mostrar solicitudes agrupadas
    for request in sorted(requests, key=lambda x: x.requested_date or date.min, reverse=True):
        _render_request_card(request, pickup_service)


def _render_request_card(request, pickup_service):
    """Renderiza una tarjeta de solicitud usando StatusPresenter."""
    
    # Usar StatusPresenter en lugar de diccionarios hardcodeados
    status_icon = StatusPresenter.get_request_icon(request.status)
    status_label = StatusPresenter.get_request_label(request.status)
    is_expanded = request.status in StatusPresenter.get_expanded_states()
    
    with st.expander(
        f"{status_icon} **Solicitud #{request.id}** - {request.requested_date} | "
        f"{request.load_quantity} retiros | {status_label}",
        expanded=is_expanded
    ):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Planta:** {request.facility_name or f'ID {request.facility_id}'}")
            st.write(f"**Tipo Vehículo:** {request.vehicle_type}")
        
        with col2:
            st.write(f"**Retiros:** {request.load_quantity}")
            if request.vehicle_type == "AMPLIROLL":
                st.write(f"**Contenedores/Carga:** {request.containers_per_load or 1}")
                st.write(f"**Total Contenedores:** {request.total_containers}")
        
        with col3:
            scheduled = request.scheduled_count or 0
            st.write(f"**Programados:** {scheduled}/{request.load_quantity}")
            
            # Barra de progreso
            progress = scheduled / request.load_quantity if request.load_quantity > 0 else 0
            st.progress(progress)
        
        if request.notes:
            st.write(f"**Observaciones:** {request.notes}")
        
        # Mostrar cargas individuales
        loads = pickup_service.get_loads_for_request(request.id)
        if loads:
            st.write("---")
            st.write("**Detalle de Cargas:**")
            
            load_data = []
            for load in loads:
                # Formatear fecha y hora programada
                if load.scheduled_date:
                    # Manejar tanto datetime como string
                    if hasattr(load.scheduled_date, 'strftime'):
                        fecha_prog = load.scheduled_date.strftime("%d/%m/%Y")
                        hora_prog = load.scheduled_date.strftime("%H:%M")
                    else:
                        # Es un string, intentar parsear o mostrar directo
                        fecha_prog = str(load.scheduled_date)[:10]
                        hora_prog = str(load.scheduled_date)[11:16] if len(str(load.scheduled_date)) > 10 else "-"
                else:
                    fecha_prog = "-"
                    hora_prog = "-"
                
                load_data.append({
                    "ID": load.id,
                    "Estado": StatusPresenter.get_load_display(load.status),
                    "Fecha Prog.": fecha_prog,
                    "Hora Prog.": hora_prog,
                    "Vehículo": f"ID {load.vehicle_id}" if load.vehicle_id and load.vehicle_id > 0 else "Pendiente",
                    "Destino": "Asignado" if (load.destination_site_id and load.destination_site_id > 0) else "Pendiente"
                })
            
            st.dataframe(load_data, width='stretch', hide_index=True)


def _get_allowed_vehicle_types(facility):
    """Obtiene los tipos de vehículos permitidos para una planta."""
    if facility.allowed_vehicle_types:
        return VehicleType.from_csv(facility.allowed_vehicle_types)
    else:
        # Si no hay restricción, permitir todos
        return list(VehicleType)

"""
Dispatch View - Despacho de camiones (Vista Conductor).

Responsabilidad única: Permitir al conductor visualizar viajes asignados
a su vehículo, aceptar el viaje y registrar datos de despacho.

Flujo:
1. Seleccionar patente (vehículo)
2. Ver viajes asignados a esa patente
3. Seleccionar viaje → Ver origen/destino/fecha (no editable)
4. Aceptar viaje → Habilita campos de ticket, guía, peso, pH, humedad
5. Para origen=planta de tratamiento: seleccionar contenedores 1 y 2
6. Confirmar despacho → Viaje pasa a EN_ROUTE_DESTINATION
"""

import streamlit as st
from datetime import datetime
from typing import Optional, List, Any, Dict
from domain.logistics.dtos import DispatchExecutionDTO


def dispatch_page(container):
    """
    Dispatch truck page - Vista del conductor para despacho de cargas.
    
    Args:
        container: Contenedor de servicios inyectado
    """
    st.title("🚛 Despacho de Camión")
    st.markdown("**Vista Conductor:** Aceptar viajes asignados y registrar datos de despacho")
    
    # Inicializar estado de sesión
    _init_session_state()
    
    # Cargar datos maestros
    master_data = _load_master_data(container)
    if master_data is None:
        return
    
    vehicles, drivers = master_data
    
    # Step 1: Seleccionar patente
    selected_vehicle = _render_vehicle_selector(vehicles)
    if selected_vehicle is None:
        return
    
    st.divider()
    
    # Step 2: Mostrar viajes asignados a esta patente
    assigned_loads = _get_assigned_loads_for_vehicle(container, selected_vehicle.id)
    
    if not assigned_loads:
        st.info(f"✅ No hay viajes asignados para la patente **{selected_vehicle.license_plate}**")
        _show_help_message()
        return
    
    st.success(f"📋 Hay **{len(assigned_loads)}** viaje(s) asignado(s) para **{selected_vehicle.license_plate}**")
    
    # Step 3: Renderizar cada viaje como una tarjeta expandible
    for load in assigned_loads:
        _render_trip_card(container, load, drivers)


def _init_session_state():
    """Inicializa el estado de sesión para la vista."""
    if 'accepted_trips' not in st.session_state:
        st.session_state.accepted_trips = set()


def _load_master_data(container):
    """Carga los datos maestros necesarios para el despacho."""
    try:
        vehicles = container.vehicle_service.get_all() if hasattr(container, 'vehicle_service') else []
        drivers = container.driver_service.get_all() if hasattr(container, 'driver_service') else []
    except Exception as e:
        st.error(f"Error cargando datos maestros: {str(e)}")
        return None
    
    if not vehicles:
        st.warning("⚠️ No hay vehículos configurados. Configure vehículos en **Configuración**.")
        return None
    
    return vehicles, drivers


def _render_vehicle_selector(vehicles: List[Any]) -> Optional[Any]:
    """Renderiza el selector de patente (vehículo)."""
    st.subheader("🚗 Seleccione su Vehículo")
    
    # Crear diccionario patente -> vehículo
    vehicle_options = {v.license_plate: v for v in vehicles}
    
    selected_plate = st.selectbox(
        "Patente del Camión",
        options=list(vehicle_options.keys()),
        format_func=lambda p: f"{p} ({vehicle_options[p].type})",
        help="Seleccione la patente de su vehículo para ver los viajes asignados"
    )
    
    return vehicle_options.get(selected_plate) if selected_plate else None


def _get_assigned_loads_for_vehicle(container, vehicle_id: int) -> List[Any]:
    """Obtiene las cargas asignadas para un vehículo específico."""
    try:
        logistics_service = container.logistics_service
        # Obtener cargas con status ASSIGNED o ACCEPTED para este vehículo
        return logistics_service.get_assigned_loads_by_vehicle(vehicle_id)
    except AttributeError:
        # Fallback: obtener todas las asignables y filtrar
        try:
            all_assigned = logistics_service.get_assignable_loads(vehicle_id)
            return [l for l in all_assigned if l.vehicle_id == vehicle_id]
        except Exception as e:
            st.error(f"Error obteniendo viajes: {e}")
            return []
    except Exception as e:
        st.error(f"Error obteniendo viajes asignados: {e}")
        return []


def _render_trip_card(container, load: Any, drivers: List[Any]) -> None:
    """Renderiza una tarjeta de viaje con formulario de despacho."""
    # Obtener nombres de origen/destino
    origin_name = _get_origin_name(container, load)
    dest_name = _get_destination_name(container, load)
    
    # Verificar si el viaje ya fue aceptado en esta sesión o tiene status ACCEPTED
    is_accepted = load.id in st.session_state.accepted_trips or load.status == 'ACCEPTED'
    
    card_title = f"📦 Viaje #{load.id} - {origin_name} → {dest_name}"
    
    with st.expander(card_title, expanded=True):
        # Info del viaje (no editable)
        _render_trip_info(load, origin_name, dest_name, drivers)
        
        st.divider()
        
        # Formulario de despacho
        _render_dispatch_form(container, load, drivers, is_accepted)


def _render_trip_info(load: Any, origin_name: str, dest_name: str, drivers: List[Any]) -> None:
    """Muestra la información del viaje (solo lectura)."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📍 Origen:**")
        st.info(origin_name)
        
    with col2:
        st.markdown("**🎯 Destino:**")
        st.info(dest_name)
        
    with col3:
        st.markdown("**📅 Fecha Programada:**")
        scheduled = load.scheduled_date
        if scheduled:
            if hasattr(scheduled, 'strftime'):
                st.info(scheduled.strftime("%d/%m/%Y %H:%M"))
            else:
                st.info(str(scheduled))
        else:
            st.info("Sin fecha asignada")
    
    # Info adicional
    col4, col5 = st.columns(2)
    with col4:
        driver_name = next((d.name for d in drivers if d.id == load.driver_id), f"ID: {load.driver_id}")
        st.markdown(f"**👤 Conductor asignado:** {driver_name}")
    with col5:
        st.markdown(f"**📊 Estado:** `{load.status}`")


def _render_dispatch_form(container, load: Any, drivers: List[Any], is_accepted: bool) -> None:
    """Renderiza el formulario de despacho."""
    
    # Si no está aceptado, mostrar botón de aceptar
    if not is_accepted and load.status == 'ASSIGNED':
        st.markdown("### ✋ Paso 1: Aceptar Viaje")
        if st.button(f"✅ Aceptar Viaje #{load.id}", key=f"accept_{load.id}", type="primary"):
            _handle_accept_trip(container, load.id)
        return
    
    # Si está aceptado (o ya tiene status ACCEPTED), mostrar formulario de despacho
    st.markdown("### 📝 Paso 2: Registrar Datos de Despacho")
    
    # Detectar si el origen es una planta de tratamiento
    is_from_treatment_plant = load.origin_treatment_plant_id is not None
    
    # Obtener contenedores disponibles si es desde planta de tratamiento
    available_containers = []
    if is_from_treatment_plant:
        container_tracking_service = getattr(container, 'container_tracking_service', None)
        if container_tracking_service:
            available_containers = container_tracking_service.get_dispatchable_records(
                load.origin_treatment_plant_id
            )
    
    with st.form(f"dispatch_form_{load.id}"):
        # Conductor (lista desplegable como respaldo)
        driver_idx = 0
        if drivers:
            driver_ids = [d.id for d in drivers]
            if load.driver_id in driver_ids:
                driver_idx = driver_ids.index(load.driver_id)
        
        selected_driver = st.selectbox(
            "👤 Conductor",
            options=drivers if drivers else [],
            index=driver_idx,
            format_func=lambda d: d.name,
            key=f"driver_{load.id}",
            help="Conductor asignado al viaje"
        )
        
        # ===============================================
        # Sección de Contenedores (solo para plantas de tratamiento)
        # ===============================================
        container_1_record_id = None
        container_2_record_id = None
        
        if is_from_treatment_plant:
            st.divider()
            st.markdown("#### 📦 Selección de Contenedores")
            st.info(
                "🚛 Desde planta de tratamiento siempre salen **2 contenedores**. "
                "Seleccione los contenedores que está despachando."
            )
            
            if not available_containers:
                st.warning("⚠️ No hay contenedores disponibles para despacho en esta planta.")
            else:
                col_c1, col_c2 = st.columns(2)
                
                # Crear opciones de contenedores con info de pH
                container_options = {
                    0: "-- Seleccionar --"
                }
                for rec in available_containers:
                    ph_info = f"pH₀:{rec.ph_0h:.1f}"
                    if rec.ph_2h:
                        ph_info += f" pH₂:{rec.ph_2h:.1f}"
                    if rec.ph_24h:
                        ph_info += f" pH₂₄:{rec.ph_24h:.1f}"
                    container_options[rec.id] = f"{rec.container_code} ({ph_info})"
                
                with col_c1:
                    container_1_record_id = st.selectbox(
                        "📦 Contenedor 1 *",
                        options=list(container_options.keys()),
                        format_func=lambda x: container_options[x],
                        key=f"container1_{load.id}",
                        help="Primer contenedor a despachar"
                    )
                
                with col_c2:
                    # Filtrar opciones para contenedor 2 (excluir el seleccionado en 1)
                    container_2_options = {k: v for k, v in container_options.items() 
                                          if k != container_1_record_id or k == 0}
                    container_2_record_id = st.selectbox(
                        "📦 Contenedor 2 *",
                        options=list(container_2_options.keys()),
                        format_func=lambda x: container_2_options[x],
                        key=f"container2_{load.id}",
                        help="Segundo contenedor a despachar"
                    )
        
        st.divider()
        
        # Campos de despacho
        col1, col2 = st.columns(2)
        
        with col1:
            ticket_number = st.text_input(
                "🎫 Número de Ticket",
                placeholder="Ej: TKT-001",
                key=f"ticket_{load.id}",
                help="Número de ticket de pesaje"
            )
            
            weight_net = st.number_input(
                "⚖️ Peso Neto (kg)",
                min_value=0.0,
                max_value=50000.0,
                value=0.0,
                step=100.0,
                key=f"weight_{load.id}",
                help="Peso neto de la carga en kilogramos"
            )
            
            ph = st.number_input(
                "🧪 pH",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.1,
                key=f"ph_{load.id}",
                help="pH de la carga"
            )
        
        with col2:
            guide_number = st.text_input(
                "📄 Número de Guía",
                placeholder="Ej: GD-2024-001",
                key=f"guide_{load.id}",
                help="Número de guía de transporte"
            )
            
            # Espacio vacío para alinear
            st.write("")
            st.write("")
            
            humidity = st.number_input(
                "💧 Humedad (%)",
                min_value=0.0,
                max_value=100.0,
                value=80.0,
                step=0.1,
                key=f"humidity_{load.id}",
                help="Porcentaje de humedad de la carga"
            )
        
        st.divider()
        
        # Botón de despacho
        submit = st.form_submit_button("🚀 Confirmar Despacho", type="primary")
        
        if submit:
            _handle_dispatch_submit(
                container, 
                load.id,
                selected_driver.id if selected_driver else load.driver_id,
                ticket_number,
                guide_number,
                weight_net,
                ph,
                humidity,
                is_from_treatment_plant,
                container_1_record_id if is_from_treatment_plant else None,
                container_2_record_id if is_from_treatment_plant else None
            )


def _handle_accept_trip(container, load_id: int) -> None:
    """Maneja la aceptación de un viaje."""
    try:
        logistics_service = container.logistics_service
        logistics_service.accept_trip(load_id)
        st.session_state.accepted_trips.add(load_id)
        st.success(f"✅ Viaje #{load_id} aceptado. Ahora puede ingresar los datos de despacho.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al aceptar viaje: {e}")


def _handle_dispatch_submit(
    container,
    load_id: int,
    driver_id: int,
    ticket_number: str,
    guide_number: str,
    weight_net: float,
    ph: float,
    humidity: float,
    is_from_treatment_plant: bool = False,
    container_1_record_id: Optional[int] = None,
    container_2_record_id: Optional[int] = None
) -> None:
    """Procesa el formulario de despacho."""
    # Validaciones
    if not ticket_number:
        st.error("❌ Debe ingresar el número de ticket")
        return
    if not guide_number:
        st.error("❌ Debe ingresar el número de guía")
        return
    if weight_net <= 0:
        st.error("❌ El peso neto debe ser mayor a 0")
        return
    
    # Validaciones para despacho desde planta de tratamiento
    if is_from_treatment_plant:
        if not container_1_record_id or container_1_record_id == 0:
            st.error("❌ Debe seleccionar el Contenedor 1")
            return
        if not container_2_record_id or container_2_record_id == 0:
            st.error("❌ Debe seleccionar el Contenedor 2")
            return
        if container_1_record_id == container_2_record_id:
            st.error("❌ No puede seleccionar el mismo contenedor dos veces")
            return
    
    try:
        # Create DTO (Pydantic validation)
        dto = DispatchExecutionDTO(
            load_id=load_id,
            ticket_number=ticket_number,
            guide_number=guide_number,
            weight_net=weight_net,
            quality_ph=ph,
            quality_humidity=humidity,
            container_1_id=container_1_record_id if is_from_treatment_plant else None,
            container_2_id=container_2_record_id if is_from_treatment_plant else None
        )
        
        # Use Application Service
        if hasattr(container, 'logistics_app_service'):
            container.logistics_app_service.execute_dispatch(dto)
        else:
            # Fallback to legacy logic
            logistics_service = container.logistics_service
            
            dispatch_data = {
                'ticket_number': ticket_number,
                'guide_number': guide_number,
                'weight_net': weight_net,
                'quality_ph': ph,
                'quality_humidity': humidity,
            }
            
            logistics_service.close_trip(load_id, dispatch_data)
            
            if is_from_treatment_plant:
                container_tracking_service = getattr(container, 'container_tracking_service', None)
                if container_tracking_service:
                    try:
                        container_tracking_service.mark_as_dispatched(
                            record_id=container_1_record_id,
                            load_id=load_id,
                            container_position=1
                        )
                        container_tracking_service.mark_as_dispatched(
                            record_id=container_2_record_id,
                            load_id=load_id,
                            container_position=2
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Contenedores despachados pero error al actualizar registro: {e}")
        
        # Limpiar del estado de sesión
        st.session_state.accepted_trips.discard(load_id)
        
        st.success(f"✅ ¡Despacho confirmado! Viaje #{load_id} en ruta hacia destino.")
        st.rerun()
        
    except ValueError as e:
        st.error(f"❌ Error de validación: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        with st.expander("Detalles del error"):
            st.exception(e)


def _get_origin_name(container, load: Any) -> str:
    """Obtiene el nombre del origen de la carga."""
    try:
        if load.origin_facility_id:
            facility = container.facility_service.get_by_id(load.origin_facility_id)
            if facility:
                return facility.name
        if load.origin_treatment_plant_id:
            plant = container.treatment_plant_service.get_by_id(load.origin_treatment_plant_id)
            if plant:
                return plant.name
    except Exception:
        pass
    return f"Origen #{load.origin_facility_id or load.origin_treatment_plant_id or 'N/A'}"


def _get_destination_name(container, load: Any) -> str:
    """Obtiene el nombre del destino de la carga."""
    try:
        if load.destination_site_id:
            site = container.location_service.get_site_by_id(load.destination_site_id)
            if site:
                return f"🏔️ {site.name} (Disposición)"
        if load.destination_treatment_plant_id:
            plant = container.treatment_plant_service.get_by_id(load.destination_treatment_plant_id)
            if plant:
                return f"🏭 {plant.name} (Tratamiento)"
    except Exception:
        pass
    
    if load.destination_site_id:
        return f"Predio #{load.destination_site_id}"
    if load.destination_treatment_plant_id:
        return f"Planta #{load.destination_treatment_plant_id}"
    return "Destino no definido"


def _show_help_message():
    """Muestra mensaje de ayuda cuando no hay viajes."""
    with st.expander("ℹ️ ¿Cómo funciona?"):
        st.markdown("""
        **Flujo de Despacho:**
        1. Los viajes se programan en el módulo de **Planificación**
        2. Al asignar un viaje a un vehículo, aparecerá aquí
        3. Seleccione su patente para ver los viajes asignados
        4. Acepte el viaje y complete los datos de despacho
        5. Al confirmar, el viaje pasará a estado "En Ruta"
        
        **Siguiente paso:**
        - Si el destino es un **predio de disposición** → aparecerá en **Disposición Final > Recepción**
        - Si el destino es una **planta de tratamiento** → aparecerá en **Tratamiento > Recepción**
        """)

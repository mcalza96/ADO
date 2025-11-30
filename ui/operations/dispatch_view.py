import streamlit as st
import pandas as pd
from datetime import datetime
from container import get_container
from ui.styles import apply_industrial_style

def dispatch_view():
    """
    Vista del Conductor "Mi Ruta".
    Flujo lineal: Scheduled -> Accepted -> InTransit -> Arrived -> Delivered.
    """
    apply_industrial_style()
    st.title("🚛 Mi Ruta")
    
    # Dependency Injection
    services = get_container()
    transport_service = services.transport_service
    dispatch_service = services.dispatch_service
    location_service = services.location_service
    
    # --- 1. Selector de Vehículo ---
    # Load active vehicles
    vehicles = transport_service.get_all_active_vehicles()
    
    if not vehicles:
        st.error("No hay vehículos activos registrados en el sistema.")
        return

    vehicle_opts = [v.license_plate for v in vehicles]
    
    # Session State for persistence
    if 'selected_vehicle_plate' not in st.session_state:
        st.session_state['selected_vehicle_plate'] = vehicle_opts[0] if vehicle_opts else None
        
    # Sidebar or Top Selector? Top is better for mobile focus
    selected_plate = st.selectbox(
        "Vehículo / Patente",
        options=vehicle_opts,
        index=vehicle_opts.index(st.session_state['selected_vehicle_plate']) if st.session_state['selected_vehicle_plate'] in vehicle_opts else 0,
        key='vehicle_selector'
    )
    
    # Update session state
    st.session_state['selected_vehicle_plate'] = selected_plate
    
    if not selected_plate:
        return

    # --- 2. Obtener Cargas ---
    loads = transport_service.get_driver_loads(selected_plate)
    
    if not loads:
        st.info(f"✅ No tienes viajes pendientes para la patente {selected_plate}.")
        st.caption("Tus asignaciones aparecerán aquí.")
        return
        
    # Focus on the first active load for the linear flow
    # In a real scenario, we might want to let them pick if multiple exist, 
    # but "Mi Ruta" implies a sequence. We'll take the first one.
    current_load = loads[0]
    
    # Get Context Data
    origin_facility = services.location_service.get_facility_by_id(current_load.origin_facility_id)
    destination_site = location_service.get_site_by_id(current_load.destination_site_id)
    
    origin_name = origin_facility.name if origin_facility else "Origen Desconocido"
    dest_name = destination_site.name if destination_site else "Destino Desconocido"
    
    # --- 3. Flujo de Estados ---
    
    st.divider()
    
    # STATUS: SCHEDULED
    if current_load.status == 'Scheduled':
        st.header("📅 Nuevo Viaje Asignado")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Origen", origin_name)
        with col2:
            st.metric("Destino", dest_name)
            
        st.info("Por favor, confirma que aceptas este viaje.")
        
        if st.button("👍 Aceptar Viaje", use_container_width=True, type="primary"):
            try:
                dispatch_service.accept_trip(current_load.id)
                st.success("Viaje aceptado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al aceptar: {str(e)}")

    # STATUS: ACCEPTED (En Planta Origen)
    elif current_load.status == 'Accepted':
        st.header("🏭 En Planta de Origen")
        st.subheader(f"Cargando en: {origin_name}")
        
        st.warning("⚠️ Espera a que termine la carga y te entreguen la documentación.")
        
        st.markdown(f"**Destino:** {dest_name}")
        
        if st.button("🚚 Salir de Planta (Iniciar Ruta)", use_container_width=True, type="primary"):
            try:
                dispatch_service.start_route(current_load.id)
                st.success("Ruta iniciada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al iniciar ruta: {str(e)}")

    # STATUS: IN TRANSIT (En Ruta)
    elif current_load.status == 'InTransit':
        st.header("🛣️ En Ruta")
        st.subheader(f"Hacia: {dest_name}")
        
        st.info("Conduce con precaución.")
        
        # Show some details
        with st.expander("Ver Detalles de Carga"):
            st.write(f"**ID Carga:** {current_load.id}")
            st.write(f"**Producto/Lote:** {current_load.batch_id}") # Could fetch batch code
            st.write(f"**Peso Neto:** {current_load.weight_net} kg")
            st.write(f"**Guía:** {current_load.guide_number}")
        
        if st.button("🏁 Llegué a Destino", use_container_width=True, type="primary"):
            try:
                dispatch_service.register_arrival(current_load.id)
                st.success("Llegada registrada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar llegada: {str(e)}")

    # STATUS: ARRIVED (En Destino - Cierre)
    elif current_load.status == 'Arrived':
        st.header("🏁 En Destino")
        st.subheader(f"Llegaste a: {dest_name}")
        
        st.markdown("### 📝 Cierre de Viaje / Entrega")
        
        with st.form("close_trip_form"):
            st.write("Ingresa los datos finales de la entrega:")
            
            c1, c2 = st.columns(2)
            with c1:
                guide_input = st.text_input("Nro Guía Despacho", value=current_load.guide_number or "")
                ticket_input = st.text_input("Nro Ticket Báscula")
            with c2:
                weight_input = st.number_input("Peso Neto (kg)", min_value=0.0, step=10.0, value=current_load.weight_net or 0.0)
            
            c3, c4 = st.columns(2)
            with c3:
                ph_input = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
            with c4:
                humidity_input = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1)
                
            submit_close = st.form_submit_button("✅ Cerrar Viaje y Entregar", use_container_width=True, type="primary")
            
            if submit_close:
                if not guide_input or not ticket_input or weight_input <= 0:
                    st.error("Por favor completa Guía, Ticket y Peso válido.")
                else:
                    try:
                        data = {
                            'weight_net': weight_input,
                            'ticket_number': ticket_input,
                            'guide_number': guide_input,
                            'quality_ph': ph_input,
                            'quality_humidity': humidity_input
                        }
                        dispatch_service.close_trip(current_load.id, data)
                        st.balloons()
                        st.success(f"Carga entregada exitosamente en {dest_name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al cerrar viaje: {str(e)}")

    else:
        st.error(f"Estado de carga desconocido: {current_load.status}")

if __name__ == "__main__":
    dispatch_view()

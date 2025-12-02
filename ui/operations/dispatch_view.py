import streamlit as st
import pandas as pd
from datetime import datetime
from container import get_container
from ui.styles import apply_industrial_style

def dispatch_view(vehicle_service, dispatch_service, location_service, treatment_plant_service):
    """
    Vista del Conductor "Mi Ruta".
    Flujo lineal: Scheduled -> Accepted -> InTransit -> Arrived -> Delivered.
    """
    apply_industrial_style()
    st.title("🚛 Mi Ruta")
    
    # Dependency Injection
    
    # --- 1. Selector de Vehículo ---
    # Load active vehicles
    vehicles = vehicle_service.get_all_vehicles(active_only=True)
    
    if not vehicles:
        st.error("No hay vehículos activos registrados en el sistema.")
        return

    vehicle_map = {v.license_plate: v for v in vehicles}
    vehicle_opts = list(vehicle_map.keys())
    
    # Session State for persistence
    if 'selected_vehicle_plate' not in st.session_state:
        st.session_state['selected_vehicle_plate'] = vehicle_opts[0] if vehicle_opts else None
        
    # Sidebar or Top Selector? Top is better for mobile focus
    selected_plate = st.selectbox(
        "Soy el Conductor del Vehículo:",
        options=vehicle_opts,
        index=vehicle_opts.index(st.session_state['selected_vehicle_plate']) if st.session_state['selected_vehicle_plate'] in vehicle_opts else 0,
        key='vehicle_selector'
    )
    
    # Update session state
    st.session_state['selected_vehicle_plate'] = selected_plate
    
    if not selected_plate:
        return

    selected_vehicle = vehicle_map[selected_plate]

    # --- 2. Obtener Cargas ---
    # Use new repository methods
    # Check for Active Load (InTransit or Arrived)
    active_load = dispatch_service.load_repo.get_active_load(selected_vehicle.id)
    current_load = active_load

    # Check for Scheduled Loads (Assigned to this vehicle but not started)
    scheduled_loads = dispatch_service.load_repo.get_assignable_loads(selected_vehicle.id)
    if scheduled_loads:
        # Show list to accept
        st.info(f"Tienes {len(scheduled_loads)} viaje(s) asignado(s).")
        
        # Display cards for scheduled loads
        for load in scheduled_loads:
            # Resolve names
            origin_name = "N/A"
            if load.origin_facility_id:
                fac = treatment_plant_service.get_by_id(load.origin_facility_id)
                origin_name = fac.name if fac else str(load.origin_facility_id)
            
            dest_name = "N/A"
            if load.destination_site_id:
                site = location_service.site_repo.get_by_id(load.destination_site_id)
                dest_name = site.name if site else str(load.destination_site_id)
            elif load.destination_treatment_plant_id: # Assuming this field exists in Load
                 # If destination is a plant (internal transfer)
                 plant = treatment_plant_service.get_by_id(load.destination_treatment_plant_id)
                 dest_name = plant.name if plant else str(load.destination_treatment_plant_id)

            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**Origen:** {origin_name}")
                    st.markdown(f"**Destino:** {dest_name}")
                    st.caption(f"ID: {load.id} | Fecha: {load.scheduled_date}")
                with c2:
                    if st.button("👍 Aceptar", key=f"accept_{load.id}", use_container_width=True, type="primary"):
                        try:
                            dispatch_service.accept_trip(load.id)
                            st.success("Viaje aceptado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            return
        else:
            st.success(f"✅ No tienes viajes pendientes para la patente {selected_plate}.")
            st.caption("Tus asignaciones aparecerán aquí.")
            return

    # Extract data from dict (repo returns dicts now)
    if current_load:
        load_id = current_load.id
        status = current_load.status
        
        # Resolve names for current load
        origin_name = "Origen Desconocido"
        if current_load.origin_facility_id:
            fac = treatment_plant_service.get_by_id(current_load.origin_facility_id)
            origin_name = fac.name if fac else str(current_load.origin_facility_id)
            
        dest_name = "Destino Desconocido"
        if current_load.destination_site_id:
            site = location_service.site_repo.get_by_id(current_load.destination_site_id)
            dest_name = site.name if site else str(current_load.destination_site_id)
    else:
        st.error("No se pudo cargar la información del viaje activo.")
        return
    
    # --- 3. Flujo de Estados ---
    
    st.divider()
    
    # STATUS: ACCEPTED (En Planta Origen)
    if status == 'Accepted':
        st.header("🏭 En Planta de Origen")
        st.subheader(f"Cargando en: {origin_name}")
        
        st.warning("⚠️ Espera a que termine la carga y te entreguen la documentación.")
        
        st.markdown(f"**Destino:** {dest_name}")
        
        if st.button("🚚 Iniciar Ruta (Ya cargué)", use_container_width=True, type="primary"):
            try:
                dispatch_service.start_trip(load_id)
                st.success("Ruta iniciada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al iniciar ruta: {str(e)}")

    # STATUS: IN TRANSIT (En Ruta)
    elif status == 'InTransit':
        st.header("🛣️ En Ruta")
        st.subheader(f"Hacia: {dest_name}")
        
        st.info("Conduce con precaución.")
        
        # Show some details
        with st.expander("Ver Detalles de Carga"):
            st.write(f"**ID Carga:** {load_id}")
            st.write(f"**Producto/Lote:** {current_load.get('batch_id', 'N/A')}") 
            st.write(f"**Peso Neto Estimado:** {current_load.get('weight_net', 0)} kg")
            st.write(f"**Guía:** {current_load.get('guide_number', 'Pendiente')}")
        
        st.markdown("### 🏁 Llegada a Destino")
        
        if st.button("🏁 Llegué a Portería", use_container_width=True, type="primary"):
            try:
                # Register arrival without data (TTO-03 update)
                dispatch_service.register_arrival(load_id)
                st.success("Llegada registrada.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar llegada: {str(e)}")

    # STATUS: ARRIVED (En Destino - Cierre)
    elif status == 'Arrived':
        st.header("🏁 En Destino")
        st.subheader(f"Llegaste a: {dest_name}")
        
        st.markdown("### 📝 Recepción y Cierre (TTO-03)")
        
        with st.form("close_trip_form"):
            st.write("Ingresa los datos finales de recepción:")
            
            st.markdown("#### Documentación y Pesaje")
            c1, c2 = st.columns(2)
            with c1:
                ticket_input = st.text_input("Nro Ticket Báscula")
                guide_input = st.text_input("Nro Guía Despacho", value=current_load.get('guide_number') or "")
            with c2:
                weight_input = st.number_input("Peso Neto Final (kg)", min_value=0.0, step=10.0, value=float(current_load.get('weight_net') or 0.0))
            
            st.markdown("#### Calidad Final")
            c3, c4 = st.columns(2)
            with c3:
                ph_input = st.number_input("pH Final (5.0 - 9.0)", min_value=0.0, max_value=14.0, step=0.1, value=float(current_load.get('quality_ph') or 7.0))
            with c4:
                humidity_input = st.number_input("Humedad Final (%)", min_value=0.0, max_value=100.0, step=0.1, value=float(current_load.get('quality_humidity') or 50.0))
                
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
                        dispatch_service.close_trip(load_id, data)
                        st.balloons()
                        st.success(f"Carga entregada exitosamente en {dest_name}!")
                        st.rerun()
                    except ValueError as ve:
                        st.error(f"Error de validación: {str(ve)}")
                    except Exception as e:
                        st.error(f"Error al cerrar viaje: {str(e)}")

    else:
        st.error(f"Estado de carga desconocido: {status}")

if __name__ == "__main__":
    dispatch_view()

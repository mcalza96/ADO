"""
Example Module: Logistics Operations

This module demonstrates the registry pattern for self-registering UI modules.

Key Concepts:
1. Module imports registry
2. Defines page functions
3. Self-registers at module level
4. main.py doesn't need to know about this module

To add this module to the app:
    # In main.py, just import the module
    import ui.modules.logistics  # That's it! Auto-registered
"""

import streamlit as st
from ui.registry import UIRegistry, MenuItem
from pydantic import ValidationError
from domain.shared.commands import (
    CreateLoadCommand,
    DispatchTruckCommand,
    RegisterArrivalCommand
)


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def dispatch_page(container):
    """
    Dispatch truck page - demonstrates Command Object usage.
    
    This replaces passing 20+ parameters to service methods.
    """
    st.title("🚛 Despacho de Camión")
    st.markdown("**Actividad:** Despachar carga hacia predio de disposición")
    
    # Get master data - using flat container structure
    try:
        batches = []  # TODO: Get from batch_service when available
        drivers = container.driver_service.get_all() if hasattr(container, 'driver_service') else []
        vehicles = container.vehicle_service.get_all() if hasattr(container, 'vehicle_service') else []
        sites = container.location_service.get_all_sites() if hasattr(container, 'location_service') else []
        facilities = container.facility_service.get_all() if hasattr(container, 'facility_service') else []
    except Exception as e:
        st.error(f"Error cargando datos maestros: {str(e)}")
        return
    
    if not all([drivers, vehicles, sites, facilities]):
        st.warning("⚠️ Debe configurar conductores, vehículos, predios y plantas en **Configuración** primero")
        with st.expander("ℹ️ Datos disponibles"):
            st.write(f"Conductores: {len(drivers)}")
            st.write(f"Vehículos: {len(vehicles)}")
            st.write(f"Predios: {len(sites)}")
            st.write(f"Plantas: {len(facilities)}")
        return
    
    # Form
    with st.form("dispatch_form"):
        st.subheader("Datos del Despacho")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Origen**")
            facility_idx = st.selectbox(
                "Planta",
                range(len(facilities)),
                format_func=lambda i: facilities[i].name
            )
            facility = facilities[facility_idx] if facilities else None
            
        with col2:
            st.markdown("**Destino**")
            site_idx = st.selectbox(
                "Predio",
                range(len(sites)),
                format_func=lambda i: f"{sites[i].name}"
            )
            site = sites[site_idx] if sites else None
        
        st.divider()
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            driver_idx = st.selectbox(
                "Conductor",
                range(len(drivers)),
                format_func=lambda i: drivers[i].name
            )
            driver = drivers[driver_idx] if drivers else None
        
        with col4:
            vehicle_idx = st.selectbox(
                "Vehículo",
                range(len(vehicles)),
                format_func=lambda i: f"{vehicles[i].license_plate}"
            )
            vehicle = vehicles[vehicle_idx] if vehicles else None
        
        with col5:
            weight = st.number_input(
                "Peso Neto (kg)",
                min_value=0.0,
                max_value=50000.0,
                value=15000.0,
                step=100.0
            )
        
        guide_number = st.text_input("Nº Guía Transporte (opcional)")
        
        submit = st.form_submit_button("🚀 Despachar", type="primary")
    
    if submit:
        try:
            # For now, create a simple dispatch without batch
            # TODO: Integrate with batch system
            if not all([driver, vehicle, site, facility]):
                st.error("❌ Debe seleccionar todos los campos")
                return
            
            # Call dispatch service directly
            result = container.dispatch_service.create_dispatch(
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                destination_site_id=site.id,
                origin_facility_id=facility.id,
                weight_net=weight,
                guide_number=guide_number if guide_number else None
            )
            
            if result:
                st.success(f"✅ Despacho creado exitosamente!")
                st.balloons()
            else:
                st.error(f"❌ Error al crear despacho")
                
        except ValidationError as e:
            # Pydantic validation errors
            st.error("❌ Errores de validación:")
            for error in e.errors():
                field = ' → '.join(str(loc) for loc in error['loc'])
                st.error(f"**{field}**: {error['msg']}")
                
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            with st.expander("Detalles del error"):
                st.exception(e)


def reception_page(container):
    """Reception at site - Gate In."""
    st.title("📦 Recepción en Predio")
    st.markdown("**Actividad:** Registrar llegada y pesaje en báscula")
    
    # Get loads in transit
    try:
        loads_in_transit = container.dispatch_service.get_loads_by_status("IN_TRANSIT") if hasattr(container, 'dispatch_service') else []
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar las cargas en tránsito: {str(e)}")
        loads_in_transit = []
    
    if not loads_in_transit:
        st.info("✅ No hay cargas en tránsito")
        return
    
    st.success(f"📦 {len(loads_in_transit)} carga(s) en tránsito")
    
    for load in loads_in_transit:
        with st.expander(f"🚛 Carga #{load.id} - {load.manifest_code}", expanded=True):
            st.markdown(f"**Conductor:** {load.driver_id}")
            st.markdown(f"**Vehículo:** {load.vehicle_id}")
            st.markdown(f"**Peso Estimado:** {load.weight_net:.0f} kg")
            
            with st.form(f"reception_{load.id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    arrival_time = st.datetime_input(
                        "Hora de Llegada",
                        value=st.session_state.get(f'arrival_{load.id}', None)
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
                try:
                    # Create Command Object
                    command = RegisterArrivalCommand(
                        load_id=load.id,
                        arrival_time=arrival_time,
                        weight_gross=weight_gross if weight_gross > 0 else None,
                        ph=ph if ph else None,
                        humidity=humidity if humidity else None,
                        observation=observation if observation else None
                    )
                    
                    # Call service
                    success = container.logistics.dispatch_service.register_arrival(
                        load_id=command.load_id,
                        weight_gross=command.weight_gross,
                        ph=command.ph,
                        humidity=command.humidity,
                        observation=command.observation
                    )
                    
                    if success:
                        st.success(f"✅ Llegada registrada para carga {load.id}")
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar llegada")
                        
                except ValidationError as e:
                    st.error("❌ Errores de validación:")
                    for error in e.errors():
                        st.error(f"**{error['loc'][0]}**: {error['msg']}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def planning_page(container):
    """Load planning and scheduling."""
    st.title("📋 Planificación de Cargas")
    st.markdown("**Actividad:** Crear y programar solicitudes de transporte")
    
    st.info("🚧 Módulo en desarrollo")
    st.markdown("""
    **Funcionalidades planificadas:**
    - Vista de calendario semanal
    - Asignación de rutas óptimas
    - Balance de capacidad de vehículos
    - Restricciones de disponibilidad
    """)


def tracking_page(container):
    """Real-time load tracking."""
    st.title("📍 Seguimiento de Cargas")
    st.markdown("**Actividad:** Monitorear cargas en tiempo real")
    
    # Get all active loads
    try:
        loads = []
        if hasattr(container, 'dispatch_service'):
            loads = container.dispatch_service.get_loads_by_status("IN_TRANSIT")
    except Exception as e:
        st.warning(f"⚠️ Error al cargar seguimiento: {str(e)}")
        loads = []
    
    if not loads:
        st.info("✅ No hay cargas en tránsito")
        return
    
    st.metric("Cargas en Tránsito", len(loads))
    
    for load in loads:
        with st.expander(f"🚛 {load.manifest_code}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Destino", load.destination_site_id or load.treatment_plant_id)
                st.metric("Conductor", load.driver_id)
            
            with col2:
                st.metric("Peso", f"{load.weight_net:.0f} kg")
                st.metric("Estado", load.status)
            
            with col3:
                if hasattr(load, 'dispatch_time') and load.dispatch_time:
                    st.metric("Despachado", load.dispatch_time.strftime("%H:%M"))
                if hasattr(load, 'eta') and load.eta:
                    st.metric("ETA", load.eta.strftime("%H:%M"))


# ============================================================================
# MODULE REGISTRATION
# ============================================================================

# Register all pages in this module
# This happens when the module is imported (in main.py)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Despacho",
        icon="🚛",
        page_func=dispatch_page,
        permission_required="dispatch",
        order=10,
        description="Despachar cargas hacia predios",
        visible_for_roles=["Admin", "Operador", "Planificador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Recepción en Campo",
        icon="📦",
        page_func=reception_page,
        permission_required="reception",
        order=20,
        description="Registrar llegada de cargas",
        visible_for_roles=["Admin", "Operador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Planificación",
        icon="📋",
        page_func=planning_page,
        permission_required="planning",
        order=5,
        description="Planificar transportes",
        visible_for_roles=["Admin", "Planificador"]
    )
)

UIRegistry.register(
    category="Operaciones Logísticas",
    item=MenuItem(
        title="Seguimiento",
        icon="📍",
        page_func=tracking_page,
        permission_required="tracking",
        order=30,
        description="Rastrear cargas en tiempo real",
        visible_for_roles=None  # Visible for all
    )
)


# Alternative: Using decorator syntax
# @UIRegistry.auto_register("Operaciones", "Despacho", "🚛", order=10, roles=["admin", "operator"])
# def dispatch_page(container):
#     ...

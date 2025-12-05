"""
Pickup Requests View - Solicitudes de retiro de clientes.

Responsabilidad única: Mostrar y gestionar las solicitudes de retiro
pendientes creadas por los clientes.
"""

import streamlit as st


def pickup_requests_page(container):
    """
    Página de solicitudes de retiro de clientes.
    
    Args:
        container: Contenedor de servicios inyectado
    """
    st.markdown("### 📋 Solicitudes de Retiro de Clientes")
    st.info("💡 Las solicitudes las crean los clientes desde **Solicitudes > Solicitud de Retiros**")
    
    # Obtener solicitudes pendientes
    pending_requests = _get_pending_requests(container)
    
    if not pending_requests:
        st.success("✅ No hay solicitudes pendientes de clientes")
        return
    
    st.metric("Solicitudes Pendientes", len(pending_requests))
    
    for request in pending_requests:
        _render_request_card(container, request)


def _get_pending_requests(container):
    """Obtiene las solicitudes de retiro pendientes."""
    try:
        pickup_service = container.pickup_request_service
        return pickup_service.get_pending_requests()
    except Exception as e:
        st.warning(f"⚠️ Error al cargar solicitudes: {str(e)}")
        return []


def _render_request_card(container, request):
    """Renderiza una tarjeta de solicitud de retiro."""
    header = (
        f"📦 Solicitud #{request.id} - {request.requested_date} | "
        f"{request.load_quantity} retiros ({request.vehicle_type})"
    )
    
    with st.expander(header, expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Cliente:** ID {request.client_id}")
            st.write(f"**Planta:** ID {request.facility_id}")
        
        with col2:
            st.write(f"**Tipo Vehículo:** {request.vehicle_type}")
            st.write(f"**Retiros:** {request.load_quantity}")
            if request.containers_per_load:
                st.write(f"**Contenedores/carga:** {request.containers_per_load}")
        
        with col3:
            scheduled = request.scheduled_count or 0
            pending = request.load_quantity - scheduled
            st.write(f"**Programados:** {scheduled}")
            st.write(f"**Pendientes:** {pending}")
        
        if request.notes:
            st.write(f"**Notas:** {request.notes}")
        
        # Mostrar cargas individuales para esta solicitud
        _render_pending_loads(container, request)


def _render_pending_loads(container, request):
    """Renderiza las cargas pendientes de asignar para una solicitud."""
    try:
        pickup_service = container.pickup_request_service
        loads = pickup_service.get_loads_for_request(request.id)
        pending_loads = [l for l in loads if l.status in ['REQUESTED', 'CREATED']]
        
        if pending_loads:
            st.write("---")
            st.write(f"**{len(pending_loads)} cargas pendientes de asignar:**")
            
            for load in pending_loads[:5]:  # Mostrar primeras 5
                container_info = ""
                if load.container_quantity:
                    container_info = f" ({load.container_quantity} cont.)"
                    
                st.caption(f"• Carga #{load.id} - {request.vehicle_type}{container_info}")
                
    except Exception as e:
        st.warning(f"Error al cargar cargas: {str(e)}")

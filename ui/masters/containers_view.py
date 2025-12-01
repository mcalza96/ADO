import streamlit as st
from models.masters.container import Container


def render(container_service, contractor_service):
    """
    Vista de gestión de Contenedores (Tolvas) con inyección de dependencias.
    
    Args:
        container_service: ContainerService instance
        contractor_service: ContractorService instance (needed for contractor dropdown)
    """
    st.title("📦 Gestión de Contenedores (Tolvas)")
    
    # Initialize session state
    if 'container_edit_id' not in st.session_state:
        st.session_state['container_edit_id'] = None
    
    # Get contractors for dropdown
    contractors = contractor_service.get_all_contractors(active_only=True)
    
    # Create New Container Section
    with st.expander("➕ Nuevo Contenedor", expanded=False):
        if not contractors:
            st.warning("⚠️ No hay contratistas activos. Debe crear un contratista antes de registrar contenedores.")
        else:
            with st.form("new_container"):
                st.subheader("Datos del Contenedor")
                
                code = st.text_input(
                    "Código del Contenedor *", 
                    placeholder="ej. TOLVA-204",
                    help="Código visual pintado en el contenedor"
                )
                
                # Contractor dropdown
                contractor_opts = {f"{c.name} ({c.rut or 'Sin RUT'})": c.id for c in contractors}
                sel_contractor = st.selectbox("Contratista *", list(contractor_opts.keys()))
                
                capacity_m3 = st.number_input(
                    "Capacidad (m³) *", 
                    min_value=5.0, 
                    max_value=40.0, 
                    value=20.0, 
                    step=1.0,
                    help="Capacidad volumétrica entre 5 y 40 m³"
                )
                
                status = st.selectbox(
                    "Estado Inicial",
                    ["AVAILABLE", "MAINTENANCE", "DECOMMISSIONED"],
                    help="AVAILABLE: Disponible para uso | MAINTENANCE: En mantenimiento | DECOMMISSIONED: Dado de baja"
                )
                
                if st.form_submit_button("Crear Contenedor"):
                    if not code or not code.strip():
                        st.error("El código del contenedor es obligatorio.")
                    else:
                        try:
                            container = Container(
                                id=None,
                                contractor_id=contractor_opts[sel_contractor],
                                code=code.strip(),
                                capacity_m3=capacity_m3,
                                status=status
                            )
                            container_service.save(container)
                            st.success(f"✅ Contenedor {code} creado exitosamente ({capacity_m3}m³)")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ Error de validación: {e}")
                        except Exception as e:
                            st.error(f"❌ Error al crear contenedor: {e}")
    
    st.divider()
    
    # Filter Options
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_contractor = st.selectbox(
            "Filtrar por Contratista",
            ["Todos"] + [c.name for c in contractors] if contractors else ["Todos"],
            key="filter_contractor"
        )
    with col2:
        show_inactive = st.checkbox("Mostrar Inactivos", value=False)
    
    # List Containers
    if filter_contractor == "Todos":
        containers = container_service.get_all_containers(active_only=not show_inactive)
    else:
        contractor_id = next((c.id for c in contractors if c.name == filter_contractor), None)
        if contractor_id:
            containers = container_service.get_by_contractor(contractor_id, active_only=not show_inactive)
        else:
            containers = []
    
    if not containers:
        st.info("📦 No hay contenedores registrados con los filtros seleccionados.")
        return
    
    st.subheader(f"Contenedores Registrados ({len(containers)})")
    
    # Display containers with actions
    data = []
    for c in containers:
        # Format status with emoji
        status_emoji = {
            'AVAILABLE': '✅',
            'MAINTENANCE': '🔧',
            'DECOMMISSIONED': '🚫'
        }
        
        data.append({
            "ID": c.id,
            "Código": c.code,
            "Display": c.display_name,
            "Contratista": c.contractor_name or "N/A",
            "Capacidad (m³)": c.capacity_m3,
            "Estado": f"{status_emoji.get(c.status, '❓')} {c.status}",
            "Activo": "✓" if c.is_active else "✗"
        })
    
    st.dataframe(data, use_container_width=True)
    
    # Actions section
    st.divider()
    with st.expander("🔧 Acciones sobre Contenedores"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cambiar Estado")
            container_ids = {f"{c.code} - {c.display_name}": c.id for c in containers if c.is_active}
            if container_ids:
                sel_container_status = st.selectbox("Seleccionar Contenedor", list(container_ids.keys()), key="status_change")
                new_status = st.selectbox("Nuevo Estado", ["AVAILABLE", "MAINTENANCE", "DECOMMISSIONED"], key="new_status")
                
                if st.button("Actualizar Estado"):
                    try:
                        container_id = container_ids[sel_container_status]
                        container = container_service.get_container_by_id(container_id)
                        if container:
                            container.status = new_status
                            container_service.save(container)
                            st.success(f"✅ Estado actualizado a {new_status}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.info("No hay contenedores activos")
        
        with col2:
            st.subheader("Eliminar Contenedor (Soft Delete)")
            if container_ids:
                sel_container_delete = st.selectbox("Seleccionar Contenedor", list(container_ids.keys()), key="delete_select")
                
                if st.button("🗑️ Desactivar Contenedor", type="secondary"):
                    try:
                        container_id = container_ids[sel_container_delete]
                        container_service.delete_container(container_id)
                        st.success("✅ Contenedor desactivado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.info("No hay contenedores activos")

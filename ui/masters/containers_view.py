"""
Container Management View - Using GenericMasterView pattern

Gestión de contenedores (tolvas) con soporte para:
- CRUD básico via GenericMasterView
- Filtrado por contratista
- Acciones adicionales (cambio de estado)
"""

import streamlit as st
from domain.logistics.entities.container import Container
from ui.generic_master_view import GenericMasterView, FieldConfig
from ui.utils.inputs import select_entity
from ui.presenters.status_presenter import StatusPresenter, ContainerStatus
from ui.constants import OperationalThresholds


def render(container_service, contractor_service):
    """
    Vista de gestión de Contenedores (Tolvas) con inyección de dependencias.
    
    Args:
        container_service: ContainerService instance
        contractor_service: ContractorService instance (needed for contractor dropdown)
    """
    st.title("📦 Gestión de Contenedores (Tolvas)")
    
    # Check if we have contractors (required for containers)
    contractors = contractor_service.get_all_contractors(active_only=True)
    if not contractors:
        st.warning("⚠️ No hay contratistas activos. Debe crear un contratista antes de registrar contenedores.")
        return
    
    # Create tabs for organization
    tab_list, tab_new, tab_actions = st.tabs([
        "📋 Lista de Contenedores",
        "➕ Nuevo Contenedor", 
        "🔧 Acciones"
    ])
    
    with tab_list:
        _render_container_list(container_service, contractor_service, contractors)
    
    with tab_new:
        _render_new_container_form(container_service, contractors)
    
    with tab_actions:
        _render_container_actions(container_service, contractors)


def _render_container_list(container_service, contractor_service, contractors):
    """Render the list of containers with filters."""
    # Filter Options
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_contractor = st.selectbox(
            "Filtrar por Contratista",
            ["Todos"] + [c.name for c in contractors],
            key="filter_contractor_list"
        )
    with col2:
        show_inactive = st.checkbox("Mostrar Inactivos", value=False)
    
    # Get filtered containers
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
    
    # Build display data usando StatusPresenter
    data = [{
        "ID": c.id,
        "Código": c.code,
        "Display": c.display_name,
        "Contratista": c.contractor_name or "N/A",
        "Capacidad (m³)": c.capacity_m3,
        "Estado": StatusPresenter.get_container_display(c.status),
        "Activo": StatusPresenter.format_boolean(c.is_active)
    } for c in containers]
    
    st.dataframe(data, width='stretch', hide_index=True)


def _render_new_container_form(container_service, contractors):
    """Render the new container form."""
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
            min_value=OperationalThresholds.MIN_CONTAINER_CAPACITY, 
            max_value=OperationalThresholds.MAX_CONTAINER_CAPACITY, 
            value=OperationalThresholds.DEFAULT_CONTAINER_CAPACITY, 
            step=1.0,
            help=f"Capacidad volumétrica entre {OperationalThresholds.MIN_CONTAINER_CAPACITY} y {OperationalThresholds.MAX_CONTAINER_CAPACITY} m³"
        )
        
        # Use Enum for status
        status = st.selectbox(
            "Estado Inicial",
            [s.value for s in ContainerStatus],
            help=f"{ContainerStatus.AVAILABLE.value}: {StatusPresenter.get_container_description(ContainerStatus.AVAILABLE.value)} | "
                 f"{ContainerStatus.MAINTENANCE.value}: {StatusPresenter.get_container_description(ContainerStatus.MAINTENANCE.value)} | "
                 f"{ContainerStatus.DECOMMISSIONED.value}: {StatusPresenter.get_container_description(ContainerStatus.DECOMMISSIONED.value)}"
        )
        
        if st.form_submit_button("💾 Crear Contenedor", type="primary"):
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


def _render_container_actions(container_service, contractors):
    """Render container actions section."""
    # Get active containers for actions
    containers = container_service.get_all_containers(active_only=True)
    
    if not containers:
        st.info("No hay contenedores activos para gestionar.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cambiar Estado")
        container_opts = {f"{c.code} - {c.display_name}": c.id for c in containers}
        
        sel_container = st.selectbox(
            "Seleccionar Contenedor", 
            list(container_opts.keys()), 
            key="status_change_container"
        )
        new_status = st.selectbox(
            "Nuevo Estado", 
            [s.value for s in ContainerStatus], 
            key="new_status_select"
        )
        
        if st.button("✅ Actualizar Estado", width='stretch'):
            try:
                container_id = container_opts[sel_container]
                container = container_service.get_container_by_id(container_id)
                if container:
                    container.status = new_status
                    container_service.save(container)
                    st.success(f"✅ Estado actualizado a {StatusPresenter.get_container_display(new_status)}")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        st.subheader("Desactivar Contenedor")
        
        sel_container_delete = st.selectbox(
            "Seleccionar Contenedor", 
            list(container_opts.keys()), 
            key="delete_select_container"
        )
        
        st.warning("Esta acción desactivará el contenedor (soft delete).")
        
        if st.button("🗑️ Desactivar", width='stretch', type="secondary"):
            try:
                container_id = container_opts[sel_container_delete]
                container_service.delete_container(container_id)
                st.success("✅ Contenedor desactivado")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

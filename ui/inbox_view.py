"""
Inbox View - Vista de bandeja de entrada de tareas pendientes.

Refactorizado para:
- Usar AppState para manejo de session state
- Recibir container como dependencia inyectada
- Usar presentadores para formateo
"""

import streamlit as st
from ui.state import AppState
from ui.components.forms import get_form_renderer
from ui.presenters.status_presenter import StatusPresenter
from domain.logistics.entities.load_status import LoadStatus
from domain.shared.exceptions import TransitionException, DomainException


def inbox_page(container, user_role: str, user_id: int):
    """
    Página de bandeja de entrada de tareas pendientes.
    
    Args:
        container: Contenedor de servicios inyectado
        user_role: Rol del usuario actual
        user_id: ID del usuario actual
    """
    st.title("📥 Mi Bandeja de Entrada")
    
    # 1. Obtener servicios del container inyectado
    resolver = container.task_resolver
    
    # 2. Obtener tareas con manejo de errores
    try:
        tasks = resolver.get_pending_tasks(user_role, user_id)
    except Exception as e:
        st.error(f"❌ Error al cargar tareas: {str(e)}")
        st.caption("Por favor, contacte al administrador del sistema.")
        return
    
    if not tasks:
        st.success("🎉 ¡No tienes tareas pendientes!")
        st.info("Cuando haya tareas nuevas, aparecerán aquí automáticamente.")
        return

    # 3. Layout: Sidebar (Lista) vs Main (Formulario)
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Pendientes ({len(tasks)})")
    
    # Crear opciones de radio con diseño mejorado (usando StatusPresenter)
    task_options = {}
    for t in tasks:
        icon = StatusPresenter.get_priority_icon(t.priority)
        task_options[t.id] = f"{icon} {t.title}"
    
    # Persistir selección en session_state usando AppState
    AppState.init_if_missing(AppState.SELECTED_TASK_ID, tasks[0].id)
    
    selected_task_id = st.sidebar.radio(
        "Seleccione una tarea", 
        options=list(task_options.keys()),
        format_func=lambda x: task_options[x],
        key='task_selector',
        index=list(task_options.keys()).index(AppState.get(AppState.SELECTED_TASK_ID)) 
              if AppState.get(AppState.SELECTED_TASK_ID) in task_options else 0
    )
    
    # Actualizar session_state usando AppState
    AppState.set(AppState.SELECTED_TASK_ID, selected_task_id)
    
    # 4. Encontrar objeto tarea seleccionado
    selected_task = next((t for t in tasks if t.id == selected_task_id), None)
    
    if selected_task:
        _render_task_detail(container, selected_task, user_role, user_id)


def _render_task_detail(container, task, user_role: str, user_id: int):
    """Renderiza el detalle de una tarea seleccionada."""
    # Usar StatusPresenter para obtener configuración de prioridad
    config = StatusPresenter.get_priority_config(task.priority)
    
    # Header con indicadores visuales
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"## {config['icon']} {task.title}")
    with col2:
        st.metric("Prioridad", task.priority)
    with col3:
        st.metric("Est. Tiempo", config['estimate'])
    
    st.markdown(f"*{task.description}*")
    st.divider()
    
    # 5. Renderizar Formulario Dinámico
    render_func = get_form_renderer(task.form_type)
    
    if render_func:
        _handle_form_rendering(container, task, render_func, user_role, user_id)
    else:
        st.warning(f"⚠️ No se encontró formulario para: {task.form_type}")
        st.caption("Este tipo de tarea aún no está implementado.")


def _handle_form_rendering(container, task, render_func, user_role: str, user_id: int):
    """Maneja el renderizado y procesamiento del formulario."""
    try:
        form_data = render_func(task.payload)
        
        if form_data:
            _process_task_submission(container, task, form_data, user_role, user_id)
                        
    except Exception as e:
        st.error(f"❌ Error al renderizar formulario: {str(e)}")
        st.caption("El formulario no pudo cargarse correctamente.")


def _process_task_submission(container, task, form_data, user_role: str, user_id: int):
    """Procesa el envío del formulario de tarea."""
    with st.spinner("Procesando..."):
        try:
            if task.entity_type == "LOAD":
                _process_load_task(container, task, form_data, user_role, user_id)
            elif task.entity_type == "MACHINE":
                _process_machine_task(container, task, form_data)
                
        except TransitionException as e:
            st.error(f"❌ Error de Transición: {str(e)}")
            st.caption("La transición no es válida. Verifique el estado actual de la carga.")
            
        except DomainException as e:
            st.error(f"❌ Error de Validación: {str(e)}")
            st.caption("Los datos ingresados no cumplen con las reglas de negocio.")
            
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            st.caption("Ha ocurrido un error. Por favor, intente nuevamente o contacte al administrador.")
            import traceback
            with st.expander("🔍 Detalles Técnicos (solo para debugging)"):
                st.code(traceback.format_exc())


def _process_load_task(container, task, form_data, user_role: str, user_id: int):
    """Procesa tareas de tipo LOAD."""
    load = task.payload['load']
    target_status = LoadStatus(task.payload['target_status'])
    
    # A. Actualizar Atributos
    container.logistics_service.update_load_attributes(load.id, form_data)
    
    # B. Intentar Transición
    success = container.logistics_service.transition_load(
        load.id, 
        target_status,
        user_id=user_id,
        notes=f"Completado desde Inbox por {user_role}"
    )
    
    if success:
        st.success("✅ Tarea completada exitosamente")
        st.info(f"📊 Carga #{load.id} avanzó a estado: **{target_status.value}**")
        _clear_and_reload()
    else:
        st.warning("⚠️ La tarea se guardó pero la transición no pudo completarse automáticamente.")
        st.caption("Puede que falten otros requisitos. Verifique en el detalle de la carga.")


def _process_machine_task(container, task, form_data):
    """Procesa tareas de tipo MACHINE."""
    log_data = form_data.get('machine_log')
    if not log_data:
        st.error("❌ No se recibieron datos del formulario de maquinaria")
        return
    
    container.machinery_service.register_log(log_data)
    
    st.success("✅ Parte Diario registrado exitosamente")
    st.info(f"🚜 Máquina #{log_data['machine_id']} - Horas trabajadas: {log_data['hours_worked']:.1f}")
    _clear_and_reload()


def _clear_and_reload():
    """Limpia la selección y recarga la página."""
    AppState.clear(AppState.SELECTED_TASK_ID)
    st.rerun()

import streamlit as st
from container import get_container
from services.ui.task_resolver import TaskResolver
from ui.components.form_registry import FORM_REGISTRY
from domain.logistics.entities.load_status import LoadStatus
from domain.shared.exceptions import TransitionException, DomainException

def render_inbox_view():
    st.title("📥 Mi Bandeja de Entrada")
    
    # 1. Inicializar Servicios
    container = get_container()
    resolver = TaskResolver(container.db_manager)
    
    # 2. Obtener Tareas (Mock User)
    # En producción, esto vendría de st.session_state.user
    user_role = st.sidebar.selectbox(
        "Simular Rol", 
        ["ADMIN", "OPERATOR", "LAB_TECH", "DRIVER", "GATE_KEEPER"],
        help="Cambie el rol para ver diferentes tareas filtradas"
    )
    user_id = 1
    
    # 3. Obtener tareas con manejo de errores
    try:
        tasks = resolver.get_pending_tasks(user_role, user_id)
    except Exception as e:
        st.error(f"❌ Error al cargar tareas: {str(e)}")
        st.caption("Por favor, contacte al administrador del sistema.")
        return
    
    if not tasks:
        st.success("🎉 ¡No tienes tareas pendientes!")
        st.balloons()
        st.info("Cuando haya tareas nuevas, aparecerán aquí automáticamente.")
        return

    # 4. Layout: Sidebar (Lista) vs Main (Formulario)
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Pendientes ({len(tasks)})")
    
    # Mapeo de prioridad a colores e iconos
    priority_config = {
        "High": {"icon": "🔴", "color": "red", "estimate": "5 min"},
        "Medium": {"icon": "🟡", "color": "orange", "estimate": "3 min"},
        "Low": {"icon": "🔵", "color": "blue", "estimate": "2 min"}
    }
    
    # Crear opciones de radio con diseño mejorado
    task_options = {}
    for t in tasks:
        config = priority_config.get(t.priority, {"icon": "⚪", "estimate": "N/A"})
        task_options[t.id] = f"{config['icon']} {t.title}"
    
    # Persistir selección en session_state
    if 'selected_task_id' not in st.session_state:
        st.session_state.selected_task_id = tasks[0].id
    
    selected_task_id = st.sidebar.radio(
        "Seleccione una tarea", 
        options=list(task_options.keys()),
        format_func=lambda x: task_options[x],
        key='task_selector',
        index=list(task_options.keys()).index(st.session_state.selected_task_id) 
              if st.session_state.selected_task_id in task_options else 0
    )
    
    # Actualizar session_state
    st.session_state.selected_task_id = selected_task_id
    
    # 5. Encontrar objeto tarea seleccionado
    selected_task = next((t for t in tasks if t.id == selected_task_id), None)
    
    if selected_task:
        # Configuración de prioridad
        config = priority_config.get(selected_task.priority, {"icon": "⚪", "color": "gray", "estimate": "N/A"})
        
        # Header con indicadores visuales
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"## {config['icon']} {selected_task.title}")
        with col2:
            st.metric("Prioridad", selected_task.priority)
        with col3:
            st.metric("Est. Tiempo", config['estimate'])
        
        st.markdown(f"*{selected_task.description}*")
        st.divider()
        
        # 6. Renderizar Formulario Dinámico
        render_func = FORM_REGISTRY.get(selected_task.form_type)
        
        if render_func:
            try:
                form_data = render_func(selected_task.payload)
                
                # 7. Procesar Acción (Guardar y Transicionar)
                if form_data:
                    # Mostrar progress bar
                    with st.spinner("Procesando..."):
                        try:
                            if selected_task.entity_type == "LOAD":
                                load = selected_task.payload['load']
                                target_status = LoadStatus(selected_task.payload['target_status'])
                                
                                # A. Actualizar Atributos
                                if not load.attributes: 
                                    load.attributes = {}
                                load.attributes.update(form_data)
                                container.logistics_service.load_repo.update(load)
                                
                                # B. Intentar Transición
                                success = container.logistics_service.transition_load(
                                    load.id, 
                                    target_status,
                                    user_id=user_id,
                                    notes=f"Completado desde Inbox por {user_role}"
                                )
                                
                                if success:
                                    st.success(f"✅ Tarea completada exitosamente")
                                    st.info(f"📊 Carga #{load.id} avanzó a estado: **{target_status.value}**")
                                    st.balloons()
                                    
                                    # Limpiar selección y recargar
                                    if 'selected_task_id' in st.session_state:
                                        del st.session_state.selected_task_id
                                    st.rerun()
                                else:
                                    st.warning("⚠️ La tarea se guardó pero la transición no pudo completarse automáticamente.")
                                    st.caption("Puede que falten otros requisitos. Verifique en el detalle de la carga.")
                                    
                            elif selected_task.entity_type == "MACHINE":
                                # Crear Log
                                log_data = form_data['machine_log']
                                container.machinery_service.register_log(log_data)
                                
                                st.success("✅ Parte Diario registrado exitosamente")
                                st.info(f"🚜 Máquina #{log_data['machine_id']} - Horas trabajadas: {log_data['end_hourmeter'] - log_data['start_hourmeter']:.1f}")
                                st.balloons()
                                
                                # Limpiar selección y recargar
                                if 'selected_task_id' in st.session_state:
                                    del st.session_state.selected_task_id
                                st.rerun()
                                
                        except TransitionException as e:
                            st.error(f"❌ Error de Transición: {str(e)}")
                            st.caption("La transición no es válida. Verifique el estado actual de la carga.")
                            
                        except DomainException as e:
                            st.error(f"❌ Error de Validación: {str(e)}")
                            st.caption("Los datos ingresados no cumplen con las reglas de negocio.")
                            
                        except Exception as e:
                            st.error(f"❌ Error inesperado: {str(e)}")
                            st.caption("Ha ocurrido un error. Por favor, intente nuevamente o contacte al administrador.")
                            # Logging para debugging
                            import traceback
                            with st.expander("🔍 Detalles Técnicos (solo para debugging)"):
                                st.code(traceback.format_exc())
                                
            except Exception as e:
                st.error(f"❌ Error al renderizar formulario: {str(e)}")
                st.caption("El formulario no pudo cargarse correctamente.")
        else:
            st.warning(f"⚠️ No se encontró formulario para: {selected_task.form_type}")
            st.caption("Este tipo de tarea aún no está implementado.")

if __name__ == "__main__":
    render_inbox_view()


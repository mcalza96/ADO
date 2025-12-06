import streamlit as st
import pandas as pd
import datetime
from domain.logistics.entities.load_status import LoadStatus
from ui.components.assignment_form import render_assignment_form
from ui.presenters.planning_presenter import PlanningPresenter

# Inicializar session state para Trip Linking
def _init_trip_linking_state():
    if 'selected_primary_load' not in st.session_state:
        st.session_state.selected_primary_load = None
    if 'trip_build_mode' not in st.session_state:
        st.session_state.trip_build_mode = False
    if 'trip_candidates' not in st.session_state:
        st.session_state.trip_candidates = []

def planning_page(logistics_service, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service):
    # Inicializar estado de Trip Linking
    _init_trip_linking_state()
    
    st.title("🗓️ Tablero de Planificación (Control Tower)")

    # --- Tabs ---
    tab_backlog, tab_scheduled = st.tabs(["🔴 Por Planificar (Backlog)", "✅ Planificadas"])

    # --- Tab 1: Backlog ---
    with tab_backlog:
        # Fetch Requested Loads (Optimized)
        requested_loads = logistics_service.get_planning_loads(LoadStatus.REQUESTED.value)

        if not requested_loads:
            st.info("No hay solicitudes pendientes de planificación.")
        else:
            # Usar Presenter para transformar datos
            df = PlanningPresenter.format_backlog_loads(requested_loads)
            
            # Interactive Grid
            st.markdown("### Selecciona cargas para asignar")
            event = st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="planning_grid"
            )

            selected_rows = event.selection.rows
            
            # --- Assignment Form (Inline - debajo del grid) ---
            if selected_rows:
                selected_ids = PlanningPresenter.get_selected_load_ids(df, selected_rows)
                
                # Verificar si las cargas ya están enlazadas
                trip_id = PlanningPresenter.get_trip_id(df, selected_rows)
                
                # Buscar candidatos para enlace (solo si hay 1 carga y no tiene trip)
                linkable_candidates = None
                if len(selected_rows) == 1 and not trip_id:
                    linkable_candidates = logistics_service.find_linkable_candidates(selected_ids[0])
                
                # Callback para crear viaje enlazado
                def on_link_loads(load_ids):
                    try:
                        new_trip_id = logistics_service.link_loads_into_trip(load_ids)
                        return new_trip_id
                    except Exception as e:
                        st.error(f"❌ Error creando viaje enlazado: {e}")
                        return None
                
                # Obtener restricción de vehículos del origen
                origin_vehicle_restriction = PlanningPresenter.get_origin_vehicle_restriction(df, selected_rows)
                
                assignment_request = render_assignment_form(
                    selected_ids,
                    contractor_service,
                    driver_service,
                    vehicle_service,
                    location_service,
                    treatment_plant_service,
                    origin_allowed_vehicle_types=origin_vehicle_restriction,
                    trip_id=trip_id,
                    linkable_candidates=linkable_candidates,
                    on_link_loads=on_link_loads
                )
                
                if assignment_request:
                    try:
                        # Si hay más cargas que las seleccionadas originalmente, crear viaje enlazado primero
                        linked_count = len(assignment_request.load_ids) - len(selected_ids)
                        if linked_count > 0:
                            trip_id = logistics_service.link_loads_into_trip(assignment_request.load_ids)
                        
                        logistics_service.schedule_loads_bulk(
                            load_ids=assignment_request.load_ids,
                            driver_id=assignment_request.driver_id,
                            vehicle_id=assignment_request.vehicle_id,
                            scheduled_date=assignment_request.get_scheduled_datetime(),
                            site_id=assignment_request.site_id,
                            treatment_plant_id=assignment_request.treatment_plant_id
                        )
                        
                        # Mensaje según si hubo enlace o no
                        if linked_count > 0:
                            st.success(
                                f"✅ **Viaje enlazado programado** | "
                                f"{len(assignment_request.load_ids)} cargas → mismo destino, conductor y vehículo | "
                                f"{assignment_request.scheduled_time.strftime('%H:%M')}"
                            )
                        else:
                            st.success(f"✅ Se programaron {len(assignment_request.load_ids)} cargas para las {assignment_request.scheduled_time.strftime('%H:%M')}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error asignando cargas: {e}")

    # --- Tab 2: Scheduled ---
    with tab_scheduled:
        # Fetch Scheduled Loads (Optimized)
        scheduled_loads = logistics_service.get_planning_loads(LoadStatus.ASSIGNED.value)
        
        if not scheduled_loads:
            st.info("No hay cargas programadas.")
        else:
            # Usar Presenter para transformar datos
            df_sched = PlanningPresenter.format_scheduled_loads(scheduled_loads)
            
            st.dataframe(
                df_sched,
                width="stretch"
            )

import streamlit as st
import pandas as pd
import datetime
from domain.logistics.entities.load_status import LoadStatus
from ui.components.assignment_form import render_assignment_sidebar

def planning_page(logistics_service, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service):
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
            df = pd.DataFrame(requested_loads)
            
            # Rename for display
            df = df.rename(columns={
                'id': 'ID',
                'created_at': 'Fecha Solicitud', # Using created_at as proxy for requested_date if not present
                'origin_facility_name': 'Origen',
                'status': 'Estado'
            })
            
            # Interactive Grid
            st.markdown("### Selecciona cargas para asignar")
            event = st.dataframe(
                df[['ID', 'Fecha Solicitud', 'Origen', 'Estado']],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="planning_grid"
            )

            selected_rows = event.selection.rows
            
            # --- Assignment Form (Sidebar) ---
            if selected_rows:
                selected_indices = selected_rows
                selected_ids = df.iloc[selected_indices]["ID"].tolist()
                
                assignment_request = render_assignment_sidebar(
                    selected_ids,
                    contractor_service,
                    driver_service,
                    vehicle_service,
                    location_service,
                    treatment_plant_service
                )
                
                if assignment_request:
                    try:
                        logistics_service.schedule_loads_bulk(
                            load_ids=assignment_request.load_ids,
                            driver_id=assignment_request.driver_id,
                            vehicle_id=assignment_request.vehicle_id,
                            scheduled_date=assignment_request.scheduled_date,
                            site_id=assignment_request.site_id,
                            treatment_plant_id=assignment_request.treatment_plant_id
                        )
                        st.success(f"Se programaron {len(assignment_request.load_ids)} cargas exitosamente.")
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
            df_sched = pd.DataFrame(scheduled_loads)
            
            # Rename for display
            df_sched = df_sched.rename(columns={
                'id': 'ID',
                'scheduled_date': 'Fecha Programada',
                'origin_facility_name': 'Origen',
                'contractor_name': 'Transportista',
                'vehicle_plate': 'Patente',
                'driver_name': 'Conductor',
                'status': 'Estado'
            })
            
            # Handle destination
            df_sched['Destino'] = df_sched.apply(lambda x: x['destination_site_name'] if pd.notna(x['destination_site_name']) else x['destination_plant_name'], axis=1)
            
            st.dataframe(
                df_sched[['ID', 'Fecha Programada', 'Origen', 'Destino', 'Transportista', 'Patente', 'Conductor', 'Estado']],
                use_container_width=True
            )

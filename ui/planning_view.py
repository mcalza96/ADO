import streamlit as st
import pandas as pd
import datetime

def planning_page(logistics_service, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service):
    st.title("🗓️ Tablero de Planificación (Control Tower)")

    # --- Tabs ---
    tab_backlog, tab_scheduled = st.tabs(["🔴 Por Planificar (Backlog)", "✅ Planificadas"])

    # --- Tab 1: Backlog ---
    with tab_backlog:
        # Fetch Requested Loads (Optimized)
        requested_loads = logistics_service.get_planning_loads('Requested')

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
                
                st.sidebar.header(f"Asignando {len(selected_ids)} Cargas")
                st.sidebar.markdown(f"**IDs Seleccionados:** {', '.join(map(str, selected_ids))}")
                
                with st.sidebar.form("assignment_form"):
                    st.subheader("Recursos")
                    
                    # 1. Contractor & Driver
                    contractors = contractor_service.get_all_contractors()
                    c_opts = {c.name: c.id for c in contractors}
                    sel_c = st.selectbox("Transportista", list(c_opts.keys()))
                    
                    driver_id = None
                    vehicle_id = None
                    
                    if sel_c:
                        c_id = c_opts[sel_c]
                        drivers = driver_service.get_drivers_by_contractor(c_id)
                        d_opts = {d.name: d.id for d in drivers}
                        sel_d = st.selectbox("Conductor", list(d_opts.keys()))
                        if sel_d: driver_id = d_opts[sel_d]
                        
                        vehicles = vehicle_service.get_vehicles_by_contractor(c_id)
                        v_opts = {f"{v.license_plate} ({v.type})": v.id for v in vehicles}
                        sel_v = st.selectbox("Vehículo", list(v_opts.keys()))
                        if sel_v: vehicle_id = v_opts[sel_v]
                    
                    st.subheader("Destino")
                    dest_type = st.radio("Tipo Destino", ["Campo (Sitio)", "Planta (Tratamiento)"])
                    
                    site_id = None
                    plant_id = None
                    
                    if dest_type == "Campo (Sitio)":
                        sites = location_service.get_all_sites(active_only=True)
                        s_opts = {s.name: s.id for s in sites}
                        sel_s = st.selectbox("Predio Destino", list(s_opts.keys()))
                        if sel_s: site_id = s_opts[sel_s]
                    else:
                        plants = treatment_plant_service.get_all()
                        p_opts = {p.name: p.id for p in plants}
                        sel_p = st.selectbox("Planta Destino", list(p_opts.keys()))
                        if sel_p: plant_id = p_opts[sel_p]
                        
                    scheduled_date = st.date_input("Fecha Programada", datetime.date.today())
                    
                    if st.form_submit_button("💾 Confirmar Asignación"):
                        success_count = 0
                        for load_id in selected_ids:
                            try:
                                logistics_service.schedule_load(
                                    load_id=load_id,
                                    driver_id=driver_id,
                                    vehicle_id=vehicle_id,
                                    scheduled_date=scheduled_date,
                                    site_id=site_id,
                                    treatment_plant_id=plant_id
                                )
                                success_count += 1
                            except Exception as e:
                                st.error(f"Error asignando carga {load_id}: {e}")
                        
                        if success_count > 0:
                            st.success(f"Se programaron {success_count} cargas exitosamente.")
                            st.rerun()

    # --- Tab 2: Scheduled ---
    with tab_scheduled:
        # Fetch Scheduled Loads (Optimized)
        scheduled_loads = logistics_service.get_planning_loads('Scheduled')
        
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

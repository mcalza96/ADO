import streamlit as st
import pandas as pd
import datetime
from container import get_container
from database.db_manager import DatabaseManager
from services.operations.logistics_service import LogisticsService
from services.compliance.compliance_service import ComplianceService
from repositories.site_repository import SiteRepository
from repositories.load_repository import LoadRepository
from repositories.batch_repository import BatchRepository
from repositories.application_repository import ApplicationRepository
from services.masters.transport_service import TransportService
from services.masters.location_service import LocationService
from services.masters.treatment_plant_service import TreatmentPlantService

def planning_page(treatment_plant_service=None):
    st.title("🗓️ Tablero de Planificación (Control Tower)")

    # --- Dependency Injection via Container ---
    services = get_container()
    
    logistics_service = services.logistics_service
    transport_service = services.transport_service
    location_service = services.location_service
    # Use passed service or get from container
    treatment_plant_service = treatment_plant_service or services.treatment_plant_service

    # --- Tabs ---
    tab_backlog, tab_scheduled = st.tabs(["🔴 Por Planificar (Backlog)", "✅ Planificadas"])

    # --- Tab 1: Backlog ---
    with tab_backlog:
        # Fetch Requested Loads
        # Assuming get_by_status returns a list of Load objects
        requested_loads = logistics_service.load_repo.get_by_status('Requested')

        if not requested_loads:
            st.info("No hay solicitudes pendientes de planificación.")
        else:
            # Prepare Data for Grid
            data = []
            for load in requested_loads:
                # Resolve Origin Name
                if load.origin_facility_id:
                    fac = treatment_plant_service.get_by_id(load.origin_facility_id)
                    origin = fac.name if fac else f"Facility {load.origin_facility_id}"
                elif load.origin_treatment_plant_id:
                    plant = treatment_plant_service.get_plant_by_id(load.origin_treatment_plant_id)
                    origin = plant.name if plant else f"Plant {load.origin_treatment_plant_id}"
                else:
                    origin = "Unknown"

                data.append({
                    "ID": load.id,
                    "Fecha Solicitud": load.requested_date,
                    "Origen": origin,
                    "Volumen Est.": 20.0, # Placeholder or derived
                    "Estado": load.status
                })
            
            df = pd.DataFrame(data)

            # Configure Columns
            column_config = {
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Fecha Solicitud": st.column_config.DateColumn("Fecha Solicitud", format="DD/MM/YYYY"),
                "Volumen Est.": st.column_config.NumberColumn("Volumen (tons)", format="%.1f"),
            }

            # Interactive Grid
            st.markdown("### Selecciona cargas para asignar")
            event = st.dataframe(
                df,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                key="planning_grid"
            )

            selected_rows = event.selection.rows
            
            # --- Assignment Form (Sidebar) ---
            if selected_rows:
                selected_indices = selected_rows
                # Get the actual IDs from the dataframe using the selected indices
                # selected_rows returns a list of integer indices corresponding to the displayed dataframe
                selected_ids = df.iloc[selected_indices]["ID"].tolist()
                
                st.sidebar.header(f"Asignando {len(selected_ids)} Cargas")
                st.sidebar.markdown(f"**IDs Seleccionados:** {', '.join(map(str, selected_ids))}")
                
                with st.sidebar.form("assignment_form"):
                    st.subheader("Recursos")
                    
                    # 1. Contractor & Driver
                    contractors = transport_service.get_all_contractors()
                    c_opts = {c.name: c.id for c in contractors}
                    sel_c = st.selectbox("Transportista", list(c_opts.keys()))
                    
                    driver_id = None
                    vehicle_id = None
                    
                    if sel_c:
                        c_id = c_opts[sel_c]
                        drivers = transport_service.get_drivers_by_contractor(c_id)
                        d_opts = {d.name: d.id for d in drivers}
                        sel_d = st.selectbox("Conductor", list(d_opts.keys()))
                        if sel_d: driver_id = d_opts[sel_d]
                        
                        vehicles = transport_service.get_vehicles_by_contractor(c_id)
                        v_opts = {f"{v.license_plate} ({v.type})": v.id for v in vehicles}
                        sel_v = st.selectbox("Vehículo", list(v_opts.keys()))
                        if sel_v: vehicle_id = v_opts[sel_v]

                    st.subheader("Programación")
                    scheduled_date = st.date_input("Fecha Programada", value=datetime.date.today())
                    scheduled_time = st.time_input("Hora", value=datetime.time(8, 0))
                    
                    st.subheader("Destino")
                    # Simplified destination selection for bulk assignment
                    # Ideally this should be smart based on origin, but for bulk we might assume same destination
                    # or force user to pick one valid for all.
                    dest_type = st.radio("Tipo Destino", ["Predio", "Planta"], horizontal=True)
                    
                    site_id = None
                    plant_id = None
                    
                    if dest_type == "Predio":
                        sites = location_service.get_all_sites()
                        s_opts = {s.name: s.id for s in sites}
                        sel_s = st.selectbox("Predio Destino", list(s_opts.keys()))
                        if sel_s: site_id = s_opts[sel_s]
                    else:
                        plants = treatment_plant_service.get_all_plants()
                        p_opts = {p.name: p.id for p in plants}
                        sel_p = st.selectbox("Planta Destino", list(p_opts.keys()))
                        if sel_p: plant_id = p_opts[sel_p]

                    container_qty = st.number_input("Contenedores (por carga)", min_value=1, value=1)

                    submitted = st.form_submit_button("Confirmar Asignación")
                    
                    if submitted:
                        if not driver_id or not vehicle_id or (not site_id and not plant_id):
                            st.error("Por favor complete todos los campos requeridos.")
                        else:
                            success_count = 0
                            errors = []
                            
                            full_date = datetime.datetime.combine(scheduled_date, scheduled_time)
                            
                            progress_bar = st.progress(0)
                            
                            for idx, load_id in enumerate(selected_ids):
                                try:
                                    logistics_service.schedule_load(
                                        load_id=load_id,
                                        driver_id=driver_id,
                                        vehicle_id=vehicle_id,
                                        scheduled_date=full_date,
                                        site_id=site_id,
                                        treatment_plant_id=plant_id,
                                        container_quantity=container_qty
                                    )
                                    success_count += 1
                                except Exception as e:
                                    errors.append(f"Load {load_id}: {str(e)}")
                                
                                progress_bar.progress((idx + 1) / len(selected_ids))
                            
                            if success_count > 0:
                                st.success(f"Se asignaron {success_count} cargas exitosamente.")
                            
                            if errors:
                                st.error(f"Hubo {len(errors)} errores:")
                                for err in errors:
                                    st.write(err)
                                    
                            if success_count == len(selected_ids):
                                st.rerun()

            else:
                st.info("👆 Selecciona una o más cargas en la tabla para habilitar el panel de asignación.")

    # --- Tab 2: Scheduled ---
    with tab_scheduled:
        scheduled_loads = logistics_service.load_repo.get_by_status('Scheduled')
        if not scheduled_loads:
            st.info("No hay cargas programadas.")
        else:
            s_data = []
            for load in scheduled_loads:
                # Resolve Origin
                if load.origin_facility_id:
                    fac = treatment_plant_service.get_by_id(load.origin_facility_id)
                    origin = fac.name if fac else str(load.origin_facility_id)
                else:
                    plant = treatment_plant_service.get_plant_by_id(load.origin_treatment_plant_id)
                    origin = plant.name if plant else str(load.origin_treatment_plant_id)
                
                # Resolve Driver/Vehicle
                driver = transport_service.get_driver_by_id(load.driver_id)
                vehicle = transport_service.get_vehicle_by_id(load.vehicle_id)
                
                s_data.append({
                    "ID": load.id,
                    "Fecha Programada": load.scheduled_date,
                    "Origen": origin,
                    "Conductor": driver.name if driver else "N/A",
                    "Vehículo": vehicle.license_plate if vehicle else "N/A",
                    "Destino ID": load.destination_site_id if load.destination_site_id else load.destination_treatment_plant_id
                })
            
            df_scheduled = pd.DataFrame(s_data)
            st.dataframe(
                df_scheduled,
                use_container_width=True,
                column_config={
                    "Fecha Programada": st.column_config.DatetimeColumn("Fecha Programada", format="DD/MM/YYYY HH:mm"),
                },
                hide_index=True
            )

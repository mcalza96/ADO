import streamlit as st
import datetime
from container import get_container

def disposal_operations_page(disposal_service, location_service, driver_service, treatment_plant_service, site_prep_service):
    st.title("🏔️ Operaciones de Disposición")
    
    # 1. Context Selection (Site)
    try:
        sites = location_service.get_all_sites()
    except Exception as e:
        st.error(f"Error al cargar predios: {e}")
        return
        
    if not sites:
        st.warning("No hay predios configurados.")
        return
        
    s_opts = {s.name: s.id for s in sites}
    sel_site_name = st.selectbox("📍 Seleccione Predio de Trabajo", list(s_opts.keys()))
    site_id = s_opts[sel_site_name]
    
    st.divider()
    
    # Main Operational Tabs: Reception and Disposal
    tab_reception, tab_disposal, tab_prep, tab_close = st.tabs([
        "🚛 1. Recepción (Portería)", 
        "🚜 2. Disposición (Campo)",
        "🔧 Preparación",
        "🏁 Cierre"
    ])
    
    # ============================================
    # TAB 1: RECEPTION (Portería/Báscula) 
    # ============================================
    with tab_reception:
        st.subheader("🚛 Recepción en Portería/Báscula")
        st.markdown("**Rol:** Operario de Báscula | **Acción:** Registrar llegada y pesaje")
        
        # Auto-refresh button
        if st.button("🔄 Actualizar Cargas en Ruta", key="refresh_reception"):
            st.rerun()
        
        st.divider()
        
        # Get loads with status='Dispatched' (En Ruta)
        try:
            load_repo = disposal_service.load_repo
            dispatched_loads = load_repo.get_by_status('Dispatched')
            
            # Filter by destination site
            dispatched_loads = [l for l in dispatched_loads if l.destination_site_id == site_id]
            
        except Exception as e:
            st.error(f"Error al cargar cargas despachadas: {e}")
            dispatched_loads = []
        
        if not dispatched_loads:
            st.info("✅ No hay cargas en ruta hacia este predio.")
        else:
            st.success(f"📦 Hay {len(dispatched_loads)} carga(s) en ruta esperando recepción.")
            
            for load in dispatched_loads:
                with st.expander(f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - Peso Neto Estimado: {load.weight_net or 'N/A'} kg", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Ticket:** {load.ticket_number or 'N/A'}")
                        st.markdown(f"**Despacho:** {load.dispatch_time or 'N/A'}")
                    with c2:
                        st.markdown(f"**Conductor ID:** {load.driver_id or 'N/A'}")
                        st.markdown(f"**Vehículo ID:** {load.vehicle_id or 'N/A'}")
                    with c3:
                        st.markdown(f"**Estado:** `{load.status}`")
                        st.markdown(f"**Batch ID:** {load.batch_id or 'N/A'}")
                    
                    st.divider()
                    st.markdown("#### 📊 Registro de Ingreso (Pesaje)")
                    
                    with st.form(f"reception_form_{load.id}"):
                        r_col1, r_col2 = st.columns(2)
                        with r_col1:
                            weight_arrival = st.number_input(
                                "⚖️ Peso en Báscula (kg)", 
                                min_value=0.0, 
                                step=10.0, 
                                value=float(load.weight_net or 0.0),
                                key=f"weight_{load.id}"
                            )
                        with r_col2:
                            observation = st.text_area(
                                "📝 Observaciones de Calidad",
                                placeholder="Ej: Olor normal, consistencia adecuada...",
                                key=f"obs_{load.id}"
                            )
                        
                        submitted = st.form_submit_button("✅ Registrar Ingreso")
                        
                        if submitted:
                            try:
                                disposal_service.register_arrival(
                                    load_id=load.id,
                                    weight=weight_arrival,
                                    observation=observation if observation else None
                                )
                                st.success(f"✅ Carga #{load.id} recepcionada exitosamente. Ahora está disponible para disposición.")
                                st.rerun()
                            except ValueError as e:
                                st.error(f"❌ Error de validación: {e}")
                            except Exception as e:
                                st.error(f"❌ Error inesperado: {e}")

    # ============================================
    # TAB 2: DISPOSAL (Campo/Tractorista)
    # ============================================
    with tab_disposal:
        st.subheader("🚜 Disposición en Campo")
        st.markdown("**Rol:** Tractorista/Operador de Campo | **Acción:** Incorporar carga al suelo")
        
        # Auto-refresh button
        if st.button("🔄 Actualizar Cargas Disponibles", key="refresh_disposal"):
            st.rerun()
        
        st.divider()
        
        # Get loads ready for disposal (Status: Delivered)
        try:
            # Use the service method which now fetches 'Delivered' loads
            arrived_loads = disposal_service.get_pending_disposal_loads(site_id)
            
        except Exception as e:
            st.error(f"Error al cargar cargas para disposición: {e}")
            arrived_loads = []
            
        except Exception as e:
            st.error(f"Error al cargar cargas recepcionadas: {e}")
            arrived_loads = []
        
        if not arrived_loads:
            st.info("✅ No hay cargas recepcionadas pendientes de incorporación.")
        else:
            st.success(f"📦 Hay {len(arrived_loads)} carga(s) lista(s) para incorporar al suelo.")
            
            for load in arrived_loads:
                with st.expander(f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - Peso Real: {load.weight_gross_reception or load.weight_net or 'N/A'} kg", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Ticket:** {load.ticket_number or 'N/A'}")
                        st.markdown(f"**Llegada:** {load.arrival_time or 'N/A'}")
                    with c2:
                        st.markdown(f"**Peso Báscula:** {load.weight_gross_reception or 'N/A'} kg")
                        st.markdown(f"**Batch ID:** {load.batch_id or 'N/A'}")
                    with c3:
                        st.markdown(f"**Estado:** `{load.status}`")
                        st.markdown(f"**Obs. Recepción:** {load.reception_observations or 'N/A'}")
                    
                    # Quality Data Display with Warnings
                    st.markdown("#### 🧪 Calidad de Carga")
                    q_c1, q_c2 = st.columns(2)
                    
                    with q_c1:
                        ph_val = load.quality_ph
                        if ph_val is not None:
                            if ph_val < 6.0 or ph_val > 8.5:
                                st.warning(f"⚠️ **pH:** {ph_val} (Rango alerta)")
                            else:
                                st.success(f"✅ **pH:** {ph_val}")
                        else:
                            st.info("pH: No registrado")
                            
                    with q_c2:
                        hum_val = load.quality_humidity
                        if hum_val is not None:
                            if hum_val < 40.0 or hum_val > 90.0: # Example warning range
                                st.warning(f"⚠️ **Humedad:** {hum_val}% (Rango alerta)")
                            else:
                                st.success(f"✅ **Humedad:** {hum_val}%")
                        else:
                            st.info("Humedad: No registrado")
                    
                    st.divider()
                    st.markdown("#### 🌾 Confirmación de Incorporación")
                    
                    with st.form(f"disposal_form_{load.id}"):
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            gps_coords = st.text_input(
                                "📍 Coordenadas GPS de Incorporación", 
                                value="-33.456, -70.657",
                                placeholder="Latitud, Longitud",
                                key=f"gps_{load.id}"
                            )
                        with d_col2:
                            method = st.selectbox(
                                "🚜 Método de Aplicación", 
                                ["Inyección Directa", "Incorporación Mecánica", "Superficial"],
                                key=f"method_{load.id}"
                            )
                        
                        submitted = st.form_submit_button("✅ Confirmar Incorporación")
                        
                        if submitted:
                            try:
                                # Combine coordinates and method for now
                                final_coords = f"{gps_coords} | {method}"
                                disposal_service.execute_disposal(
                                    load_id=load.id,
                                    coordinates=final_coords
                                )
                                st.success(f"✅ Carga #{load.id} incorporada exitosamente al suelo.")
                                st.rerun()
                            except ValueError as e:
                                st.error(f"❌ Error de validación: {e}")
                            except Exception as e:
                                st.error(f"❌ Error inesperado: {e}")

    # ============================================
    # TAB 3: PREPARATION (Labores Previas)
    # ============================================
    with tab_prep:
        st.subheader("🔧 Registro de Labores Previas (DO-06 a DO-16)")
        
        with st.form("site_event_form"):
            col1, col2 = st.columns(2)
            with col1:
                evt_type = st.selectbox("Tipo de Labor", [
                    "Preparación de Suelo (Arado)", 
                    "Rastraje",
                    "Control de Vectores Inicial",
                    "Habilitación de Caminos",
                    "Construcción de Pretiles"
                ])
                evt_date = st.date_input("Fecha de Labor", datetime.date.today())
            
            with col2:
                evt_desc = st.text_area("Descripción / Observaciones")
            
            if st.form_submit_button("📝 Registrar Labor"):
                try:
                    site_prep_service.register_site_event(
                        site_id, 
                        evt_type, 
                        datetime.datetime.combine(evt_date, datetime.time(0, 0)), 
                        evt_desc
                    )
                    st.success("✅ Labor registrada correctamente.")
                except ValueError as e:
                    st.error(f"❌ Error de validación: {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")
        
        st.divider()
        st.markdown("### 📋 Historial de Labores")
        
        try:
            events = services.site_prep_service.get_site_events(site_id)
            if events:
                for evt in events:
                    st.text(f"{evt.event_date} | {evt.event_type} | {evt.description or 'Sin descripción'}")
            else:
                st.info("No hay labores registradas para este predio.")
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

    # ============================================
    # TAB 4: CLOSURE (Cierre de Faena)
    # ============================================
    with tab_close:
        st.subheader("🏁 Cierre Operativo de Faena")
        
        with st.form("closure_form"):
            c_date = st.date_input("Fecha de Cierre", datetime.date.today())
            responsible = st.text_input("Responsable de Cierre")
            
            check_sector = st.checkbox("Cierre de Paño (Sector Completo)")
            check_day = st.checkbox("Cierre de Faena (Diario)")
            
            obs = st.text_area("Observaciones de Cierre")
            
            if st.form_submit_button("🔒 Registrar Cierre"):
                try:
                    desc = f"Responsable: {responsible} | Paño: {check_sector} | Faena: {check_day} | Obs: {obs}"
                    services.site_prep_service.register_site_event(
                        site_id, 
                        "Cierre Operativo", 
                        datetime.datetime.combine(c_date, datetime.time(23, 59)), 
                        desc
                    )
                    st.success("✅ Cierre operativo registrado correctamente.")
                except ValueError as e:
                    st.error(f"❌ Error de validación: {e}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")


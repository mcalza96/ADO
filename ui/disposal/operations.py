import streamlit as st
import datetime
from container import get_container

def disposal_operations_page():
    st.title("🏔️ Operaciones de Disposición")
    
    # Get services from dependency injection container
    services = get_container()
    
    # 1. Context Selection (Site)
    sites = services.location_service.get_all_sites()
    if not sites:
        st.warning("No hay predios configurados.")
        return
        
    s_opts = {s.name: s.id for s in sites}
    sel_site_name = st.selectbox("Seleccione Predio de Trabajo", list(s_opts.keys()))
    site_id = s_opts[sel_site_name]
    
    st.divider()
    
    tab_prep, tab_exec, tab_close = st.tabs(["🚜 Preparación (Pre-Disposición)", "✅ Ejecución (Disposición)", "🏁 Cierre de Faena"])
    
    # --- TAB 1: PREPARATION ---
    with tab_prep:
        st.subheader("Registro de Labores Previas (DO-06 a DO-16)")
        
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
            
            if st.form_submit_button("Registrar Labor"):
                try:
                    services.disposal_service.register_site_event(site_id, evt_type, datetime.datetime.combine(evt_date, datetime.time(0,0)), evt_desc)
                    st.success("Labor registrada correctamente.")
                except ValueError as e:
                    st.error(f"Error de validación: {e}")
                except Exception as e:
                    st.error(f"Error inesperado: {e}")
        
        st.markdown("### Historial de Labores")
        events = services.disposal_service.get_site_events(site_id)
        # Filter for prep events if needed, or show all
        if events:
            for evt in events:
                st.text(f"{evt.event_date} | {evt.event_type} | {evt.description}")
        else:
            st.info("No hay labores registradas.")

    # --- TAB 2: EXECUTION (DISPOSAL) ---
    with tab_exec:
        st.subheader("Bandeja de Entrada en Tiempo Real (Descargas Pendientes)")
        
        # Auto-refresh button or mechanism could be added here
        if st.button("🔄 Actualizar Bandeja"):
            st.rerun()
            
        pending = services.disposal_service.get_pending_disposal_loads(site_id)
        
        if not pending:
            st.info("No hay cargas pendientes de incorporación. (Esperando descargas de transporte...)")
        else:
            st.success(f"Hay {len(pending)} cargas esperando incorporación.")
            
            for load in pending:
                with st.expander(f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - {load.weight_net} kg", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Ticket:** {load.ticket_number}")
                        st.markdown(f"**Llegada:** {load.arrival_time}")
                    with c2:
                        st.markdown(f"**Origen ID:** {load.origin_facility_id}")
                        # Ideally show Class A/B here if we fetched batch info
                    with c3:
                        st.markdown(f"**Estado:** {load.status}")

                    st.divider()
                    st.markdown("#### Registro de Incorporación")
                    
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        gps_coords = st.text_input(f"📍 Coordenadas GPS", value="-33.456, -70.657", key=f"gps_{load.id}")
                    with f_col2:
                        method = st.selectbox("Método de Incorporación", ["Inyección Directa", "Incorporación Mecánica", "Superficial"], key=f"meth_{load.id}")
                    
                    if st.button(f"✅ Confirmar Disposición (Finalizar)", key=f"fin_{load.id}"):
                        try:
                            # We can append method to description or coordinates for now
                            final_coords = f"{gps_coords} | {method}"
                            services.disposal_service.execute_disposal(load.id, final_coords)
                            st.success(f"Carga #{load.id} dispuesta e incorporada exitosamente.")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"Error de validación: {e}")
                        except Exception as e:
                            st.error(f"Error inesperado: {e}")

    # --- TAB 3: CLOSURE (DO-17, DO-21) ---
    with tab_close:
        st.subheader("Cierre Operativo de Faena")
        
        with st.form("closure_form"):
            c_date = st.date_input("Fecha de Cierre", datetime.date.today())
            responsible = st.text_input("Responsable de Cierre")
            
            check_sector = st.checkbox("Cierre de Paño (Sector Completo)")
            check_day = st.checkbox("Cierre de Faena (Diario)")
            
            obs = st.text_area("Observaciones de Cierre")
            
            if st.form_submit_button("🔒 Registrar Cierre"):
                try:
                    desc = f"Responsable: {responsible} | Paño: {check_sector} | Faena: {check_day} | Obs: {obs}"
                    services.disposal_service.register_site_event(site_id, "Cierre Operativo", datetime.datetime.combine(c_date, datetime.time(23,59)), desc)
                    st.success("Cierre operativo registrado correctamente.")
                except ValueError as e:
                    st.error(f"Error de validación: {e}")
                except Exception as e:
                    st.error(f"Error inesperado: {e}")


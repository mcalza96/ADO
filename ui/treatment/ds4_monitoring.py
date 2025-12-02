import streamlit as st
from datetime import datetime, timedelta
from ui.styles import apply_industrial_style

def ds4_monitoring_view(plant_id: int, container_service, treatment_batch_service, logistics_service):
    """DS4 Monitoring view."""
        
    st.subheader("🧪 Monitoreo DS4 (Estabilización)")
    
    ops_service = logistics_service
    
    tab1, tab2, tab3 = st.tabs(["1. Llenado (Inicio)", "2. Monitoreo (pH)", "3. Despacho (Salida)"])
    
    # --- TAB 1: FILLING ---
    with tab1:
        st.markdown("### Registro de Llenado de Contenedor")
        
        avail_containers = container_service.get_available_containers(plant_id)
        if not avail_containers:
            st.warning("No hay contenedores disponibles en esta planta.")
        else:
            c_opts = {c.code: c.id for c in avail_containers}
            sel_code = st.selectbox("Seleccione Contenedor", list(c_opts.keys()))
            
            with st.form("fill_form"):
                col1, col2 = st.columns(2)
                with col1:
                    fill_time = st.time_input("Hora de Término de Llenado", datetime.now().time())
                with col2:
                    humidity = st.number_input("Humedad (%)", 0.0, 100.0, 80.0)
                
                st.markdown("#### Mediciones de pH")
                ph_0 = st.number_input("pH Inicial (0h)", 0.0, 14.0, 12.0, help="Debe ser > 12.0 para cumplir norma")
                
                if st.form_submit_button("🔒 Cerrar Contenedor e Iniciar Proceso"):
                    # Combine date
                    dt = datetime.combine(datetime.today(), fill_time)
                    treatment_batch_service.create_batch(plant_id, c_opts[sel_code], dt, ph_0, humidity)
                    st.success("Contenedor cerrado. Iniciando cuenta regresiva de 24h.")
                    st.rerun()

    # --- TAB 2: MONITORING ---
    with tab2:
        st.markdown("### Control de pH (2h y 24h)")
        active = treatment_batch_service.get_active_batches(plant_id)
        
        if not active:
            st.info("No hay contenedores en proceso de estabilización.")
        
        for batch in active:
            # Calculate elapsed time
            now = datetime.now()
            if isinstance(batch.fill_time, str):
                try:
                    fill_dt = datetime.strptime(batch.fill_time, "%Y-%m-%d %H:%M:%S")
                except:
                    fill_dt = datetime.strptime(batch.fill_time, "%Y-%m-%d %H:%M:%S.%f")
            else:
                fill_dt = batch.fill_time
                
            elapsed = now - fill_dt
            hours_elapsed = elapsed.total_seconds() / 3600
            
            with st.expander(f"📦 Batch #{batch.id} (Contenedor {batch.container_id}) | Transcurrido: {hours_elapsed:.1f}h", expanded=True):
                st.write(f"**Término Llenado:** {fill_dt.strftime('%H:%M')} | **pH 0h:** {batch.ph_0h}")
                
                c1, c2 = st.columns(2)
                
                # 2H Check
                with c1:
                    if batch.ph_2h:
                        st.success(f"✅ pH 2h: {batch.ph_2h}")
                    else:
                        if hours_elapsed >= 2:
                            st.warning("⚠️ Medición 2h Pendiente")
                            with st.form(f"ph2_{batch.id}"):
                                val = st.number_input("pH 2h", 0.0, 14.0, 12.0, key=f"in_2_{batch.id}")
                                if st.form_submit_button("Registrar 2h"):
                                    treatment_batch_service.update_ph_2h(batch.id, val)
                                    st.rerun()
                        else:
                            st.info(f"⏳ Faltan {2 - hours_elapsed:.1f}h para medición 2h")

                # 24H Check
                with c2:
                    if batch.ph_24h:
                        st.success(f"✅ pH 24h: {batch.ph_24h}")
                    else:
                        if hours_elapsed >= 24:
                            st.warning("⚠️ Medición 24h Pendiente")
                        else:
                            st.info(f"⏳ Faltan {24 - hours_elapsed:.1f}h para 24h")
                            
                        with st.form(f"ph24_{batch.id}"):
                            val = st.number_input("pH 24h", 0.0, 14.0, 0.0, key=f"in_24_{batch.id}")
                            if st.form_submit_button("Registrar pH 24h"):
                                treatment_batch_service.update_ph_24h(batch.id, val)
                                st.success("pH 24h registrado.")
                                st.rerun()

    # --- TAB 3: DISPATCH ---
    with tab3:
        st.markdown("### Solicitar Camión de Retiro")
        st.info("Solicite camiones para retirar los contenedores listos. La asignación de contenedores específicos se realizará al momento de la carga.")
        
        with st.form("request_truck"):
            req_date = st.date_input("Fecha Solicitada", datetime.today())
            qty = st.number_input("Cantidad de Camiones", 1, 10, 1)
            
            if st.form_submit_button("🚛 Solicitar Retiro"):
                for _ in range(qty):
                    ops_service.create_request(facility_id=None, requested_date=req_date, plant_id=plant_id)
                st.success(f"Se han generado {qty} solicitudes de retiro.")
                st.rerun()

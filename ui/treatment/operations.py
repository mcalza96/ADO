
import streamlit as st
from container import get_container
from ui.treatment.ds4_monitoring import ds4_monitoring_view
from ui.styles import apply_industrial_style
import datetime

def treatment_operations_page():
    apply_industrial_style()
    st.title("🏭 Operaciones de Tratamiento")
    
    services = get_container()
    plant_service = services.treatment_plant_service
    reception_service = services.treatment_reception_service
    batch_service = services.batch_service
    
    # 1. Context Selection (Plant)
    plants = plant_service.get_all()
    if not plants:
        st.warning("No hay plantas de tratamiento configuradas.")
        return
        
    p_opts = {p.name: p.id for p in plants}
    sel_plant_name = st.selectbox("Seleccione Planta de Trabajo", list(p_opts.keys()))
    plant_id = p_opts[sel_plant_name]
    
    st.divider()
    
    # TABS - Added Batch Management
    tab_batches, tab_reception, tab_ds4 = st.tabs([
        "📦 Gestión de Lotes", 
        "📥 Recepción de Lodos", 
        "🧪 Proceso DS4 (Salida)"
    ])
    
    with tab_batches:
        st.subheader("Gestión de Lotes de Producción")
        
        # Form to create new batch
        with st.expander("➕ Crear Nuevo Lote", expanded=False):
            with st.form("new_batch_form"):
                col1, col2 = st.columns(2)
                with col1:
                    batch_code = st.text_input(
                        "Código de Lote*",
                        placeholder="ej: L-2025-11-29-A",
                        help="Código único para identificar el lote"
                    )
                    production_date = st.date_input(
                        "Fecha de Producción*",
                        value=datetime.date.today()
                    )
                with col2:
                    initial_tonnage = st.number_input(
                        "Tonelaje Inicial (kg)*",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )
                    class_type = st.selectbox(
                        "Clasificación*",
                        options=["A", "B", "NoClass"],
                        help="Clasificación del biosólido según normativa"
                    )
                
                sludge_type = st.text_input(
                    "Tipo de Lodo (opcional)",
                    placeholder="ej: Deshidratado, Estabilizado"
                )
                
                if st.form_submit_button("✅ Crear Lote", type="primary"):
                    try:
                        batch = batch_service.create_daily_batch(
                            facility_id=plant_id,
                            batch_code=batch_code,
                            production_date=production_date,
                            initial_tonnage=initial_tonnage,
                            class_type=class_type,
                            sludge_type=sludge_type if sludge_type else None
                        )
                        st.success(f"✅ Lote '{batch_code}' creado exitosamente con {initial_tonnage:,.0f} kg")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ Error: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
        
        # Table of active batches
        st.divider()
        st.markdown("### Lotes Activos")
        
        batches = batch_service.get_batches_by_facility(plant_id)
        
        if not batches:
            st.info("No hay lotes registrados para esta planta.")
        else:
            # Prepare data for display
            batch_data = []
            for b in batches:
                current = b.current_tonnage or 0
                initial = b.initial_tonnage or 0
                percentage = (current / initial * 100) if initial > 0 else 0
                
                batch_data.append({
                    "ID": b.id,
                    "Código": b.batch_code,
                    "Fecha Producción": b.production_date.strftime("%Y-%m-%d") if hasattr(b.production_date, 'strftime') else str(b.production_date),
                    "Tonelaje Inicial (kg)": f"{initial:,.0f}",
                    "Saldo Disponible (kg)": f"{current:,.0f}",
                    "% Disponible": f"{percentage:.1f}%",
                    "Clase": b.class_type or "N/A",
                    "Estado": b.status
                })
            
            # Display with column configuration
            st.dataframe(
                batch_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small"),
                    "% Disponible": st.column_config.ProgressColumn(
                        "% Disponible",
                        min_value=0,
                        max_value=100,
                        format="%.1f%%"
                    )
                }
            )
            
            # Summary metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            total_initial = sum(b.initial_tonnage or 0 for b in batches)
            total_available = sum(b.current_tonnage or 0 for b in batches)
            available_batches = sum(1 for b in batches if b.status == 'Available')
            
            with col_m1:
                st.metric("Total Lotes", len(batches))
            with col_m2:
                st.metric("Lotes Disponibles", available_batches)
            with col_m3:
                st.metric("Stock Total Disponible", f"{total_available:,.0f} kg")
    
    with tab_reception:
        st.subheader("Bandeja de Entrada (Descargas Pendientes)")
        
        if st.button("🔄 Actualizar Bandeja"):
            st.rerun()
            
        pending = reception_service.get_pending_reception_loads(plant_id)
        
        if not pending:
            st.info("No hay cargas pendientes de recepción técnica.")
        else:
            st.success(f"Hay {len(pending)} cargas esperando recepción.")
            
            for load in pending:
                with st.expander(f"🚛 Carga #{load.id} - Guía: {load.guide_number or 'S/N'} - {load.weight_net} kg", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Ticket:** {load.ticket_number}")
                        st.markdown(f"**Llegada:** {load.arrival_time}")
                    with c2:
                        st.markdown(f"**Origen ID:** {load.origin_facility_id}")
                    with c3:
                        st.markdown(f"**Estado:** {load.status}")

                    st.divider()
                    st.markdown("#### Registro de Recepción Técnica")
                    
                    with st.form(f"reception_form_{load.id}"):
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            rec_time = st.time_input("Hora Ingreso Real", datetime.datetime.now().time())
                        with col_t2:
                            dis_time = st.time_input("Hora Descarga Foso", datetime.datetime.now().time())
                        
                        st.markdown("##### Variables de Calidad")
                        col_q1, col_q2 = st.columns(2)
                        with col_q1:
                            ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1, value=7.0)
                        with col_q2:
                            humidity = st.number_input("Humedad (%)", min_value=0.0, max_value=100.0, step=0.1, value=80.0)
                        
                        if st.form_submit_button("✅ Confirmar Recepción"):
                            try:
                                # Combine with today's date for MVP simplicity, or use load date logic
                                today = datetime.date.today()
                                rec_dt = datetime.datetime.combine(today, rec_time)
                                dis_dt = datetime.datetime.combine(today, dis_time)
                                
                                reception_service.execute_reception(load.id, rec_dt, dis_dt, ph, humidity)
                                st.success(f"Carga #{load.id} recibida. Lote listo para proceso.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

    with tab_ds4:
        ds4_monitoring_view(plant_id, services)


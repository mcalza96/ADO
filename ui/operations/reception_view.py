import streamlit as st
from container import get_container
from ui.styles import apply_industrial_style
import datetime

def reception_view(reception_service, treatment_plant_service):
    """
    Vista de Recepción de Cargas (Sprint 2).
    Muestra cargas en tránsito y permite confirmar llegada con ajuste de peso.
    """
    apply_industrial_style()
    st.title("📦 Recepción de Cargas")
    
    # Use dependency injection container
    
    st.markdown("### Cargas en Tránsito")
    
    # Refresh button
    if st.button("🔄 Actualizar Lista"):
        st.rerun()
    
    # Get loads in transit
    loads = reception_service.get_in_transit_loads()
    
    if not loads:
        st.info("✅ No hay cargas pendientes de recepción.")
        return
    
    st.success(f"📊 {len(loads)} cargas en tránsito")
    
    # Display loads in table/cards
    for load in loads:
        with st.expander(
            f"🚛 Guía #{load.guide_number or load.id} - {load.weight_net or 0:,.0f} kg - Despachado: {load.dispatch_time}",
            expanded=False
        ):
            # Load details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Origen**")
                st.write(f"Facility ID: {load.origin_facility_id}")
                st.write(f"Lote ID: {load.batch_id or 'N/A'}")
                
            with col2:
                st.markdown("**Transporte**")
                st.write(f"Chofer ID: {load.driver_id}")
                st.write(f"Vehículo ID: {load.vehicle_id}")
                
            with col3:
                st.markdown("**Destino**")
                st.write(f"Sitio ID: {load.destination_site_id}")
                st.write(f"Despacho: {load.dispatch_time}")
            
            st.divider()
            
            # Reception Form
            st.markdown("#### Confirmar Recepción")
            
            with st.form(f"reception_form_{load.id}"):
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    arrival_date = st.date_input(
                        "Fecha de Llegada*",
                        value=datetime.date.today(),
                        help="Fecha real de llegada"
                    )
                    arrival_time_input = st.time_input(
                        "Hora de Llegada*",
                        value=datetime.datetime.now().time(),
                        help="Hora real de llegada"
                    )
                    arrival_time = datetime.datetime.combine(arrival_date, arrival_time_input)
                
                with col_f2:
                    estimated = load.weight_net or 0
                    final_weight = st.number_input(
                        f"Peso Final Real (kg)*",
                        min_value=0.0,
                        value=float(estimated),
                        step=100.0,
                        format="%.2f",
                        help="Peso medido al llegar a destino"
                    )
                
                # Show difference
                if final_weight != estimated:
                    difference = final_weight - estimated
                    percentage_diff = (difference / estimated * 100) if estimated > 0 else 0
                    
                    if abs(percentage_diff) > 5:
                        st.warning(
                            f"⚠️ Diferencia significativa: {difference:+,.2f} kg ({percentage_diff:+.1f}%)"
                        )
                    else:
                        st.info(
                            f"ℹ️ Diferencia: {difference:+,.2f} kg ({percentage_diff:+.1f}%)"
                        )
                
                notes = st.text_area(
                    "Notas de Recepción (opcional)",
                    placeholder="Ej: Carga en buen estado, sin novedades"
                )
                
                if st.form_submit_button("✅ Confirmar Recepción", type="primary"):
                    try:
                        with st.spinner("Procesando recepción..."):
                            # Confirm arrival
                            updated_load = reception_service.confirm_arrival(
                                load_id=load.id,
                                arrival_time=arrival_time,
                                final_weight=final_weight,
                                notes=notes if notes else None
                            )
                            
                            st.success(f"✅ Carga #{load.id} recepcionada exitosamente")
                            
                            # Show summary
                            if final_weight != estimated:
                                difference = final_weight - estimated
                                st.info(
                                    f"📊 Ajuste de inventario: {difference:+,.2f} kg "
                                    f"({'agregado' if difference > 0 else 'devuelto'} al lote #{load.batch_id})"
                                )
                            
                            st.balloons()
                            st.rerun()
                            
                    except ValueError as e:
                        st.error(f"❌ Error de validación: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    # Summary metrics at bottom
    st.divider()
    st.markdown("### Resumen")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.metric("Cargas en Tránsito", len(loads))
    
    with col_m2:
        total_tonnage = sum(load.weight_net or 0 for load in loads)
        st.metric("Tonelaje Total en Tránsito", f"{total_tonnage:,.0f} kg")

if __name__ == "__main__":
    reception_view()

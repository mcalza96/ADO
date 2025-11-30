import streamlit as st
from database.db_manager import DatabaseManager
from services.operations.batch_service import BatchService
from services.operations.dispatch_service import DispatchService
from services.masters.transport_service import TransportService 
from services.masters.location_service import LocationService
from ui.styles import apply_industrial_style
import datetime

def dispatch_view():
    """
    Vista de Despacho de Camiones (Sprint 2).
    Permite seleccionar lote, conductor y vehículo para crear un despacho
    con generación de PDF del manifiesto.
    """
    apply_industrial_style()
    st.title("🚚 Despacho de Camiones")
    
    db = DatabaseManager()
    batch_service = BatchService(db)
    dispatch_service = DispatchService(db, batch_service)
    transport_service = TransportService(db)
    location_service = LocationService(db)
    
    st.markdown("### Generar Nuevo Despacho")
    
   # Section 1: Select Batch (Cascade)
    col1, col2 = st.columns(2)
    
    with col1:
        # Get all available batches
        batches = batch_service.get_available_batches()
        
        if not batches:
            st.warning("⚠️ No hay lotes disponibles para despacho.")
            return
        
        batch_opts = {
            f"{b.batch_code} - {b.current_tonnage:,.0f} kg disponibles": b.id 
            for b in batches
        }
        sel_batch_label = st.selectbox("Seleccione Lote*", list(batch_opts.keys()))
        selected_batch_id = batch_opts[sel_batch_label]
        selected_batch = batch_service.get_batch_by_id(selected_batch_id)
        
    with col2:
        # Show batch details
        if selected_batch:
            st.metric(
                "Saldo Disponible",
                f"{selected_batch.current_tonnage:,.0f} kg",
                help=f"Tonelaje inicial: {selected_batch.initial_tonnage:,.0f} kg"
            )
            st.caption(f"🏷️ Clase: **{selected_batch.class_type}**")
    
    st.divider()
    
    # Section 2: Load Form
    st.markdown("### Datos del Viaje")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Contractor selection
        contractors = transport_service.get_all_contractors()
        if not contractors:
            st.error("No hay transportistas registrados.")
            return
        
        contractor_opts = {c.name: c.id for c in contractors}
        sel_contractor = st.selectbox("Transportista*", list(contractor_opts.keys()))
        contractor_id = contractor_opts[sel_contractor]
        
        # Driver selection (filtered by contractor)
        drivers = transport_service.get_drivers_by_contractor(contractor_id)
        if not drivers:
            st.warning(f"No hay choferes registrados para {sel_contractor}")
            driver_id = None
        else:
            driver_opts = {d.name: d.id for d in drivers}
            sel_driver = st.selectbox("Chofer*", list(driver_opts.keys()))
            driver_id = driver_opts[sel_driver]
    
    with col_b:
        # Vehicle selection (filtered by contractor)
        vehicles = transport_service.get_vehicles_by_contractor(contractor_id)
        if not vehicles:
            st.warning(f"No hay vehículos registrados para {sel_contractor}")
            vehicle_id = None
            vehicle = None
        else:
            vehicle_opts = {
                f"{v.license_plate} ({v.max_capacity:,.0f} kg)": v.id 
                for v in vehicles
            }
            sel_vehicle = st.selectbox("Vehículo*", list(vehicle_opts.keys()))
            vehicle_id = vehicle_opts[sel_vehicle]
            vehicle = transport_service.get_vehicle_by_id(vehicle_id)
        
        # Destination site
        sites = location_service.get_all_sites()
        if not sites:
            st.error("No hay sitios de destino registrados.")
            return
        
        site_opts = {s.name: s.id for s in sites}
        sel_site = st.selectbox("Sitio de Destino*", list(site_opts.keys()))
        destination_site_id = site_opts[sel_site]
        
        # --- Compliance Indicator (Sprint 3) ---
        if destination_site_id:
            try:
                cap_info = dispatch_service.compliance_service.get_nitrogen_capacity(destination_site_id)
                st.caption("📊 Capacidad de Nitrógeno (Anual)")
                
                # Progress bar color
                bar_color = "green"
                if cap_info['percent_used'] > 80:
                    bar_color = "orange"
                if cap_info['percent_used'] >= 100:
                    bar_color = "red"
                
                st.progress(cap_info['percent_used'] / 100.0)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Límite", f"{cap_info['limit_kg']:,.0f} kg")
                c2.metric("Aplicado", f"{cap_info['applied_kg']:,.0f} kg")
                c3.metric("Disponible", f"{cap_info['remaining_kg']:,.0f} kg", 
                         delta_color="normal" if cap_info['remaining_kg'] > 0 else "inverse")
            except Exception as e:
                st.warning(f"No se pudo cargar info de compliance: {str(e)}")
    
    st.divider()
    
    # Section 3: Weight and Validation
    st.markdown("### Peso Estimado")
    
    col_w1, col_w2, col_w3 = st.columns(3)
    
    with col_w1:
        weight_net = st.number_input(
            "Peso Neto Estimado (kg)*",
            min_value=0.0,
            max_value=float(selected_batch.current_tonnage) if selected_batch else 100000.0,
            step=100.0,
            value=min(10000.0, float(selected_batch.current_tonnage)) if selected_batch else 10000.0,
            format="%.2f"
        )
    
    with col_w2:
        if vehicle:
            capacity = vehicle.max_capacity
            if weight_net > capacity:
                st.error(f"⚠️ Excede capacidad: {capacity:,.0f} kg")
            else:
                percentage = (weight_net / capacity * 100) if capacity > 0 else 0
                st.success(f"✅ Uso: {percentage:.1f}% de capacidad")
    
    with col_w3:
        if selected_batch:
            remaining = selected_batch.current_tonnage - weight_net
            st.info(f"Saldo después: {remaining:,.0f} kg")
    
    st.divider()
    
    # Section 4: Dispatch Action
    guide_number = st.text_input(
        "Número de Guía (opcional)",
        placeholder="Ej: GUIA-2025-001",
        help="Si no se especifica, se generará automáticamente"
    )
    
    # Validation checks
    can_dispatch = (
        selected_batch is not None and
        driver_id is not None and
        vehicle_id is not None and
        weight_net > 0 and
        weight_net <= selected_batch.current_tonnage and
        (vehicle and weight_net <= vehicle.max_capacity)
    )
    
    if st.button("🚀 Generar Despacho", type="primary", disabled=not can_dispatch):
        try:
            with st.spinner("Validando Compliance y Generando despacho..."):
                # Call dispatch service
                result = dispatch_service.dispatch_truck(
                    batch_id=selected_batch_id,
                    driver_id=driver_id,
                    vehicle_id=vehicle_id,
                    destination_site_id=destination_site_id,
                    origin_facility_id=selected_batch.facility_id,
                    weight_net=weight_net,
                    guide_number=guide_number if guide_number else None
                )
                
                # Success message
                st.success(f"✅ Camión Despachado - Guía #{result['guide_number']}")
                
                # PDF Download Button
                if result.get('pdf_bytes'):
                    st.download_button(
                        label="📄 Descargar Manifiesto PDF",
                        data=result['pdf_bytes'],
                        file_name=f"manifiesto_{result['guide_number']}.pdf",
                        mime="application/pdf"
                    )
                    st.info(f"📁 PDF guardado en: {result.get('pdf_path', 'N/A')}")
                
                # Show updated batch balance
                updated_batch = batch_service.get_batch_by_id(selected_batch_id)
                st.metric(
                    "Nuevo Saldo del Lote",
                    f"{updated_batch.current_tonnage:,.0f} kg",
                    delta=f"-{weight_net:,.0f} kg",
                    delta_color="inverse"
                )
                
        except ValueError as e:
            err_msg = str(e)
            if "OPERACIÓN BLOQUEADA" in err_msg:
                st.error(f"🚫 {err_msg}")
                st.info("💡 Sugerencia: Revise la capacidad de nitrógeno del sitio o seleccione otro lote.")
            else:
                st.error(f"❌ Error de validación: {err_msg}")
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    if not can_dispatch:
        reasons = []
        if not selected_batch:
            reasons.append("Seleccionar lote")
        if not driver_id:
            reasons.append("Seleccionar chofer")
        if not vehicle_id:
            reasons.append("Seleccionar vehículo")
        if weight_net <= 0:
            reasons.append("Ingresar peso válido")
        elif selected_batch and weight_net > selected_batch.current_tonnage:
            reasons.append("Peso excede stock disponible")
        elif vehicle and weight_net > vehicle.max_capacity:
            reasons.append("Peso excede capacidad del vehículo")
        
        if reasons:
            st.warning(f"⚠️ Requisitos faltantes: {', '.join(reasons)}")

if __name__ == "__main__":
    dispatch_view()

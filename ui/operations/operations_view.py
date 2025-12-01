import streamlit as st
from container import get_container
from ui.styles import apply_industrial_style

def operations_page():
    apply_industrial_style()
    st.title("🚛 OPERACIONES - EJECUCIÓN")
    
    services = get_container()
    ops_service = services.operations_service
    treatment_service = services.treatment_service
    disposal_service = services.master_disposal_service
    
    # 1. Identify Driver/Load
    # In a real app, Driver logs in. Here, we select a Scheduled Load to "Claim" it.
    
    scheduled_loads = ops_service.get_loads_by_status('Scheduled')
    
    if not scheduled_loads:
        st.info("No hay cargas programadas pendientes.")
        return
        
    # Display as Cards/Buttons for easy selection
    st.subheader("Seleccione su Carga Asignada")
    
    load_opts = {f"Carga #{l.id} - Destino ID: {l.destination_site_id}": l for l in scheduled_loads}
    sel_load_key = st.selectbox("Cargas Disponibles", list(load_opts.keys()))
    
    if sel_load_key:
        load = load_opts[sel_load_key]
        
        st.info(f"🆔 ID: {load.id} | 🏭 Origen: {load.origin_facility_id} | 🚜 Destino: {load.destination_site_id}")
        
        # 2. Execution Form
        st.divider()
        st.header("Registro de Despacho")
        
        # 2. Execution Form
        st.divider()
        st.header("Registro de Despacho")
        
        # Determine if Origin is Client or Treatment Plant
        is_treatment_origin = load.origin_treatment_plant_id is not None
        
        container_1_id = None
        container_2_id = None
        
        if is_treatment_origin:
            st.info("🏭 Origen: Planta de Tratamiento - Seleccione Contenedores")
            c_service = services.container_service
            # Get containers that are READY or MONITORING (Active) at this plant
            # Ideally we should filter by 'READY' only, but user said "available/ready"
            # Let's use get_ready_containers logic or similar.
            # For now, let's fetch all containers at the plant that are IN_USE (holding a batch)
            # We need a method to get containers with active batches.
            
            # Let's fetch all containers currently at the plant
            # And filter those that have a READY batch?
            # Or just list all containers at the plant.
            
            # Simplified: List all containers currently located at the plant
            # We need to know which containers are at the plant.
            # Container entity has 'current_plant_id'.
            
            # We need a service method: get_containers_at_plant(plant_id)
            # Let's assume get_available_containers returns those with status 'AVAILABLE'
            # But here we need those with status 'IN_USE' (holding a batch) that are ready to go.
            
            batch_service = services.batch_service
            ready_batches = batch_service.get_ready_batches(load.origin_treatment_plant_id)
            
            if not ready_batches:
                st.warning("No hay contenedores listos para despacho en esta planta.")
                return
                
            # Map container IDs to Codes
            # We need to fetch container codes. This is inefficient N+1 but fine for MVP.
            # Better: batch object should have container code or we fetch all containers.
            all_containers = c_service.get_all_containers()
            c_map = {c.id: c.code for c in all_containers}
            
            ready_c_opts = {f"{c_map.get(b.container_id, 'Unknown')} (Batch {b.id})": b.container_id for b in ready_batches}
            
            c1_key = st.selectbox("Contenedor 1", ["Seleccionar..."] + list(ready_c_opts.keys()))
            if c1_key != "Seleccionar...":
                container_1_id = ready_c_opts[c1_key]
                
            c2_key = st.selectbox("Contenedor 2", ["Seleccionar..."] + list(ready_c_opts.keys()))
            if c2_key != "Seleccionar...":
                container_2_id = ready_c_opts[c2_key]

        else:
            # Client Origin Logic (Existing)
            batches = treatment_service.get_batches_by_facility(load.origin_facility_id)
            if not batches:
                st.error("No hay lotes disponibles en esta planta.")
                return
                
            b_opts = {f"{b.batch_code} (Clase {b.class_type})": b for b in batches}
            sel_batch_key = st.selectbox("LOTE (BATCH) CARGADO", list(b_opts.keys()))
            
            if sel_batch_key:
                batch = b_opts[sel_batch_key]
                # Validate Destination
                try:
                    is_valid = disposal_service.validate_application(load.destination_site_id, batch.class_type)
                    if not is_valid:
                        st.error("⛔ ALERTA: El predio destino NO acepta este tipo de lodo. Contacte a Planificación.")
                        return
                    else:
                        st.success("✅ Destino Validado")
                except Exception as e:
                    st.error(f"Error validación: {e}")
                    return

        # Inputs
        col1, col2 = st.columns(2)
        with col1:
            ticket_num = st.text_input("N° TICKET DE PESAJE")
        
        with col2:
            weight_gross = st.number_input("PESO BRUTO (Kg)", min_value=0.0, step=10.0)
            weight_tare = st.number_input("PESO TARA (Kg)", min_value=0.0, step=10.0)
            st.caption(f"Neto: {weight_gross - weight_tare} kg")

        # Finalize Button
        if st.button("✅ CONFIRMAR DESPACHO"):
            if ticket_num and weight_gross > weight_tare:
                try:
                    ops_service.register_dispatch(
                        load_id=load.id,
                        ticket=ticket_num,
                        gross=weight_gross,
                        tare=weight_tare,
                        container_1_id=container_1_id,
                        container_2_id=container_2_id
                    )
                    st.success("🎉 Despacho registrado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")
            else:
                st.warning("Verifique los datos (Ticket, Pesos).")

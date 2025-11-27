import streamlit as st
from ui.styles import apply_industrial_style
from database.db_manager import DatabaseManager
from services.operations_service import OperationsService
from services.masters.treatment_service import TreatmentService
from services.masters.disposal_service import DisposalService
from domain.logistics.rules import LogisticsRules

def operations_page():
    apply_industrial_style()
    st.title("🚛 OPERACIONES - EJECUCIÓN")
    
    db = DatabaseManager()
    ops_service = OperationsService(db)
    treatment_service = TreatmentService(db)
    disposal_service = DisposalService(db)
    
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
        
        # Batch Selection (If not assigned in planning)
        # Assuming we need to specify WHAT we are carrying exactly if not done before.
        # For MVP, let's assume we just need to validate the destination accepts the product.
        # We'll ask for the Batch here to ensure validation happens at pickup.
        
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
                guide_num = st.text_input("N° GUÍA DE DESPACHO")
                ticket_num = st.text_input("N° TICKET DE PESAJE")
            
            with col2:
                weight_tons = st.number_input("PESO NETO (Toneladas)", min_value=0.0, step=0.1, format="%.2f")
                st.caption(f"Equivalente: {weight_tons * 1000:.0f} kg")

            # Finalize Button
            if st.button("✅ CONFIRMAR Y CERRAR CARGA"):
                if guide_num and ticket_num and weight_tons > 0:
                    try:
                        # Convert Tons to Kg for consistency if needed, or store as is.
                        # Domain rules usually work in Kg, let's convert.
                        weight_kg = weight_tons * 1000
                        
                        ops_service.finalize_load(
                            load_id=load.id,
                            guide_number=guide_num,
                            ticket_number=ticket_num,
                            weight_net=weight_kg
                        )
                        st.success("🎉 Carga registrada y finalizada correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al finalizar: {e}")
                else:
                    st.warning("Complete todos los campos (Guía, Ticket, Peso).")

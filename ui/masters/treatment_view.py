import streamlit as st
from container import get_container
from models.masters.treatment_plant import TreatmentPlant
from models.masters.treatment import Batch, LabResult
import datetime

def treatment_page(treatment_plant_service=None):
    st.header("Gestión de Plantas y Tratamiento")
    
    services = get_container()
    treatment_service = services.treatment_service
    client_service = services.client_service
    location_service = services.location_service
    treatment_plant_service = treatment_plant_service or services.treatment_plant_service
    
    # 1. Select Client
    clients = client_service.get_all_clients()
    if not clients:
        st.warning("No hay clientes registrados. Vaya al módulo de Clientes.")
        return

    client_opts = {c.name: c.id for c in clients}
    selected_client_name = st.selectbox("Seleccionar Cliente (Generador)", list(client_opts.keys()))
    selected_client_id = client_opts[selected_client_name]
    
    # 2. Manage Facilities
    st.subheader(f"Plantas de {selected_client_name}")
    with st.expander("Nueva Planta"):
        with st.form("new_facility"):
            f_name = st.text_input("Nombre Planta")
            f_address = st.text_input("Dirección")
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitud", format="%.6f")
            with col2:
                lon = st.number_input("Longitud", format="%.6f")
            
            if st.form_submit_button("Guardar Planta"):
                try:
                    treatment_plant_service.create_plant(
                        name=f_name,
                        address=f_address,
                        client_id=selected_client_id,
                        latitude=lat,
                        longitude=lon
                    )
                    st.success("Planta creada")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    facilities = treatment_plant_service.get_by_client(selected_client_id)
    
    if not facilities:
        st.info("No hay plantas registradas para este cliente.")
        return

    # 3. Select Facility to manage Batches
    facility_opts = {f.name: f.id for f in facilities}
    selected_facility_name = st.selectbox("Seleccionar Planta para ver Lotes", list(facility_opts.keys()))
    selected_facility_id = facility_opts[selected_facility_name]
    
    st.divider()
    
    # 4. Manage Batches
    st.subheader(f"Lotes de Producción - {selected_facility_name}")
    
    tab_batches, tab_lab = st.tabs(["Registro de Lotes", "Resultados de Laboratorio"])
    
    with tab_batches:
        with st.expander("Nuevo Lote Diario"):
            with st.form("new_batch"):
                b_code = st.text_input("Código Lote (ej. 20231127-P1)")
                b_date = st.date_input("Fecha Producción", datetime.date.today())
                col1, col2 = st.columns(2)
                with col1:
                    b_type = st.selectbox("Tipo Lodo", ["Centrifugado", "Secado", "Compost"])
                    b_class = st.selectbox("Clase", ["B", "A"])
                with col2:
                    b_ton = st.number_input("Tonelaje Inicial Est.", min_value=0.0)
                
                if st.form_submit_button("Crear Lote"):
                    try:
                        b = Batch(id=None, facility_id=selected_facility_id, batch_code=b_code, production_date=b_date, 
                                  sludge_type=b_type, class_type=b_class, initial_tonnage=b_ton)
                        treatment_service.create_batch(b)
                        st.success("Lote creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        batches = treatment_service.get_batches_by_facility(selected_facility_id)
        if batches:
            st.dataframe([vars(b) for b in batches], use_container_width=True)
        else:
            st.info("No hay lotes registrados.")

    with tab_lab:
        if not batches:
            st.warning("Cree un lote primero.")
        else:
            batch_opts = {b.batch_code: b.id for b in batches}
            sel_batch_code = st.selectbox("Seleccionar Lote", list(batch_opts.keys()))
            sel_batch_id = batch_opts[sel_batch_code]
            
            with st.expander("Ingresar Análisis de Lab"):
                with st.form("new_lab_result"):
                    l_date = st.date_input("Fecha Muestreo", datetime.date.today())
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
                        hum = st.number_input("% Humedad", min_value=0.0, max_value=100.0)
                    with c2:
                        nit = st.number_input("Nitrógeno", min_value=0.0)
                        phos = st.number_input("Fósforo", min_value=0.0)
                    with c3:
                        coli = st.number_input("Coliformes", min_value=0.0)
                        salmo = st.checkbox("Presencia Salmonella")
                    
                    if st.form_submit_button("Guardar Análisis"):
                        try:
                            res = LabResult(id=None, batch_id=sel_batch_id, sample_date=l_date, ph=ph, humidity_percentage=hum,
                                            nitrogen=nit, phosphorus=phos, coliforms=coli, salmonella_presence=salmo)
                            treatment_service.add_lab_result(res)
                            st.success("Resultados guardados")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            results = treatment_service.get_lab_results_by_batch(sel_batch_id)
            if results:
                st.write("Historial de Análisis:")
                st.dataframe([vars(r) for r in results], use_container_width=True)

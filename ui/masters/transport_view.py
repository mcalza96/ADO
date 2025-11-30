import streamlit as st
from services.masters.transport_service import TransportService
from database.db_manager import DatabaseManager
from models.masters.transport import Contractor, Driver, Vehicle


def transport_page():
    st.header("Gestión de Transporte")
    
    db = DatabaseManager()
    transport_service = TransportService(db)
    
    tab1, tab2, tab3 = st.tabs(["Contratistas", "Choferes", "Camiones"])
    
    # --- Tab 1: Contractors ---
    with tab1:
        st.subheader("Empresas de Transporte")
        with st.expander("Nuevo Contratista"):
            with st.form("new_contractor"):
                name = st.text_input("Nombre Empresa")
                rut = st.text_input("RUT")
                contact = st.text_input("Contacto")
                phone = st.text_input("Teléfono")
                if st.form_submit_button("Guardar"):
                    try:
                        c = Contractor(id=None, name=name, rut=rut, contact_name=contact, phone=phone)
                        transport_service.create_contractor(c)
                        st.success("✅ Contratista creado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al crear contratista: {e}")
        
        contractors = transport_service.get_all_contractors()
        if contractors:
            st.dataframe([vars(c) for c in contractors], use_container_width=True)
        else:
            st.info("No hay contratistas registrados.")
    
    # --- Tab 2: Drivers ---
    with tab2:
        st.subheader("Choferes")
        if not contractors:
            st.warning("⚠️ Primero cree un contratista")
        else:
            contractor_opts = {c.name: c.id for c in contractors}
            selected_contractor_name = st.selectbox("Seleccionar Contratista", list(contractor_opts.keys()), key="driver_contractor")
            selected_contractor_id = contractor_opts[selected_contractor_name]
            
            with st.expander("Nuevo Chofer"):
                with st.form("new_driver"):
                    d_name = st.text_input("Nombre Completo")
                    d_rut = st.text_input("RUT Chofer")
                    d_license = st.text_input("Licencia")
                    d_phone = st.text_input("Teléfono")
                    if st.form_submit_button("Guardar Chofer"):
                        try:
                            d = Driver(id=None, contractor_id=selected_contractor_id, name=d_name, rut=d_rut, license_number=d_license, phone=d_phone)
                            transport_service.create_driver(d)
                            st.success("✅ Chofer creado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear chofer: {e}")

            drivers = transport_service.get_drivers_by_contractor(selected_contractor_id)
            if drivers:
                st.dataframe([vars(d) for d in drivers], use_container_width=True)
            else:
                st.info("No hay choferes para este contratista")

    # --- Tab 3: Vehicles ---
    with tab3:
        st.subheader("Flota de Camiones")
        if not contractors:
            st.warning("⚠️ Primero cree un contratista")
        else:
            # Re-use selection or create new one? Better to have independent selection or shared?
            # Let's use a new selectbox for clarity in this tab
            v_contractor_name = st.selectbox("Seleccionar Contratista", list(contractor_opts.keys()), key="vehicle_contractor")
            v_contractor_id = contractor_opts[v_contractor_name]
            
            with st.expander("Nuevo Camión"):
                with st.form("new_vehicle"):
                    col1, col2 = st.columns(2)
                    with col1:
                        plate = st.text_input("Patente")
                        brand = st.text_input("Marca")
                        year = st.number_input("Año", min_value=1990, max_value=2030, step=1, value=2020)
                    with col2:
                        tare = st.number_input("Tara (kg)", min_value=0.0, help="Peso del camión vacío")
                        cap = st.number_input("Capacidad Máx (kg)", min_value=0.0, help="Capacidad máxima de carga")
                        v_type = st.selectbox("Tipo de Camión", ["BATEA", "AMPLIROLL"])
                        model = st.text_input("Modelo")
                    
                    if st.form_submit_button("Guardar Camión"):
                        try:
                            # Validate required fields
                            if not plate:
                                st.error("⚠️ La patente es obligatoria")
                            elif tare <= 0 or cap <= 0:
                                st.error("⚠️ La tara y capacidad deben ser mayores a cero")
                            else:
                                v = Vehicle(
                                    id=None, 
                                    contractor_id=v_contractor_id, 
                                    license_plate=plate, 
                                    tare_weight=tare, 
                                    max_capacity=cap, 
                                    brand=brand, 
                                    model=model, 
                                    year=year, 
                                    type=v_type
                                )
                                transport_service.create_vehicle(v)
                                st.success("✅ Camión registrado exitosamente")
                                st.rerun()
                        except ValueError as ve:
                            # Catch the specific business rule validation error
                            st.error(f"⚠️ ERROR DE VALIDACIÓN: {ve}")
                        except Exception as e:
                            st.error(f"❌ Error al registrar camión: {e}")
            
            vehicles = transport_service.get_vehicles_by_contractor(v_contractor_id)
            if vehicles:
                st.dataframe([vars(v) for v in vehicles], use_container_width=True)
            else:
                st.info("No hay vehículos registrados para este contratista")


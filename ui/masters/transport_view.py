import streamlit as st
from models.masters.transport import Contractor
from models.masters.vehicle import Vehicle
from models.masters.driver import Driver


def render(driver_service, vehicle_service, contractor_service):
    """
    Vista de gestión de Transporte con inyección de dependencias.
    
    Args:
        driver_service: DriverService instance
        vehicle_service: VehicleService instance
        contractor_service: ContractorService instance
    """
    st.header("🚛 Gestión de Transporte")
    
    # Get contractors for use across tabs
    contractors = contractor_service.get_all_contractors(active_only=True)
    
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
                        contractor_service.save(c)
                        st.success("✅ Contratista creado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al crear contratista: {e}")
        
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
                    # Note: phone field removed from schema, using only license_number
                    if st.form_submit_button("Guardar Chofer"):
                        try:
                            d = Driver(
                                id=None, 
                                contractor_id=selected_contractor_id, 
                                name=d_name, 
                                rut=d_rut, 
                                license_number=d_license
                            )
                            driver_service.save(d)
                            st.success("✅ Chofer creado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear chofer: {e}")

            drivers = driver_service.get_drivers_by_contractor(selected_contractor_id)
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
                        cap = st.number_input("Capacidad Máx (Toneladas húmedas)", min_value=0.0, help="Capacidad máxima de carga")
                        v_type = st.selectbox("Tipo de Camión", ["BATEA", "AMPLIROLL"])
                        model = st.text_input("Modelo")
                    
                    if st.form_submit_button("Guardar Camión"):
                        try:
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
                                    capacity_wet_tons=cap,
                                    brand=brand, 
                                    model=model, 
                                    year=year, 
                                    type=v_type  # Correct field name
                                )
                                vehicle_service.save(v)
                                st.success("✅ Camión registrado exitosamente")
                                st.rerun()
                        except ValueError as ve:
                            st.error(f"⚠️ ERROR DE VALIDACIÓN: {ve}")
                        except Exception as e:
                            st.error(f"❌ Error al registrar camión: {e}")
            
            vehicles = vehicle_service.get_vehicles_by_contractor(v_contractor_id)
            if vehicles:
                st.dataframe([vars(v) for v in vehicles], use_container_width=True)
            else:
                st.info("No hay vehículos registrados para este contratista")

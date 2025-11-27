import streamlit as st
from services.masters.disposal_service import DisposalService
from services.masters.location_service import LocationService
from database.db_manager import DatabaseManager
from models.masters.location import Site
from models.masters.disposal import Plot, SoilSample
import datetime

def disposal_page():
    st.header("Gestión de Predios Agrícolas (Disposición)")
    
    db = DatabaseManager()
    disposal_service = DisposalService(db)
    location_service = LocationService(db)
    
    # 1. Manage Sites (Predios)
    st.subheader("Predios")
    with st.expander("Nuevo Predio"):
        with st.form("new_site"):
            s_name = st.text_input("Nombre Predio")
            s_owner = st.text_input("Dueño / Agricultor")
            s_region = st.selectbox("Región", ["Metropolitana", "Valparaíso", "O'Higgins", "Maule", "Biobío"])
            s_address = st.text_input("Dirección / Ubicación")
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitud", format="%.6f")
            with col2:
                lon = st.number_input("Longitud", format="%.6f")
            
            if st.form_submit_button("Guardar Predio"):
                try:
                    site = Site(id=None, name=s_name, owner_name=s_owner, address=s_address, 
                                region=s_region, latitude=lat, longitude=lon)
                    location_service.create_site(site)
                    st.success("Predio creado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    sites = location_service.get_all_sites()
    if not sites:
        st.info("No hay predios registrados.")
        return

    # 2. Select Site to manage Plots
    site_opts = {s.name: s.id for s in sites}
    selected_site_name = st.selectbox("Seleccionar Predio", list(site_opts.keys()))
    selected_site_id = site_opts[selected_site_name]
    
    st.divider()
    
    # 3. Manage Plots and Soil Samples
    st.subheader(f"Sectores del Predio: {selected_site_name}")
    
    tab_plots, tab_soil = st.tabs(["Sectores (Lotes)", "Análisis de Suelo"])
    
    with tab_plots:
        with st.expander("Nuevo Sector"):
            with st.form("new_plot"):
                p_name = st.text_input("Nombre Sector (ej. Lote Norte)")
                p_area = st.number_input("Área (Hectáreas)", min_value=0.0)
                p_crop = st.text_input("Cultivo Actual (ej. Maíz)")
                
                if st.form_submit_button("Crear Sector"):
                    try:
                        plot = Plot(id=None, site_id=selected_site_id, name=p_name, area_hectares=p_area, crop_type=p_crop)
                        disposal_service.create_plot(plot)
                        st.success("Sector creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        plots = disposal_service.get_plots_by_site(selected_site_id)
        if plots:
            st.dataframe([vars(p) for p in plots], use_container_width=True)
        else:
            st.info("No hay sectores registrados.")

    with tab_soil:
        if not plots:
            st.warning("Cree un sector primero.")
        else:
            plot_opts = {p.name: p.id for p in plots}
            sel_plot_name = st.selectbox("Seleccionar Sector", list(plot_opts.keys()))
            sel_plot_id = plot_opts[sel_plot_name]
            
            with st.expander("Ingresar Análisis de Suelo"):
                with st.form("new_soil_sample"):
                    s_date = st.date_input("Fecha Muestreo", datetime.date.today())
                    valid_date = st.date_input("Válido Hasta", datetime.date.today() + datetime.timedelta(days=365))
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        ph = st.number_input("pH Suelo", min_value=0.0, max_value=14.0, step=0.1)
                        nit = st.number_input("Nitrógeno (ppm)", min_value=0.0)
                    with c2:
                        phos = st.number_input("Fósforo (ppm)", min_value=0.0)
                        pot = st.number_input("Potasio (ppm)", min_value=0.0)
                    
                    if st.form_submit_button("Guardar Análisis"):
                        try:
                            sample = SoilSample(
                                id=None, plot_id=sel_plot_id, sampling_date=s_date, valid_until=valid_date,
                                ph=ph, nitrogen_ppm=nit, phosphorus_ppm=phos, potassium_ppm=pot
                            )
                            disposal_service.create_soil_sample(sample)
                            st.success("Análisis guardado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            samples = disposal_service.get_soil_samples_by_plot(sel_plot_id)
            if samples:
                st.dataframe([vars(s) for s in samples], use_container_width=True)
            else:
                st.info("No hay análisis de suelo vigentes.")

import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from services.operations.disposal_execution import DisposalExecutionService
from services.masters.location_service import LocationService
from services.masters.transport_service import TransportService
from services.masters.treatment_plant_service import TreatmentPlantService

def disposal_page():
    st.title("🚜 Recepción y Disposición Final (Campo)")

    # --- Dependency Injection ---
    # In a real app, this might be handled by a container
    db = DatabaseManager()
    disposal_service = DisposalExecutionService(db)
    location_service = LocationService(db)
    transport_service = TransportService(db)
    treatment_plant_service = TreatmentPlantService(db)

    # --- Context Selector (Simulation) ---
    # In production, this would be determined by the logged-in user's assigned site
    st.sidebar.header("📍 Contexto del Sitio")
    sites = location_service.get_all_sites()
    site_opts = {s.name: s.id for s in sites}
    
    if not site_opts:
        st.warning("No hay sitios configurados en el sistema.")
        return

    selected_site_name = st.sidebar.selectbox("Sitio Actual (Simulado)", list(site_opts.keys()))
    current_site_id = site_opts[selected_site_name]
    
    # Get Site Details for Map
    current_site = location_service.site_repo.get_by_id(current_site_id)

    # --- Metrics ---
    # Mocked daily total
    st.metric("Toneladas Recibidas Hoy", "120.5 tons", "+15.0 tons (última hora)")

    # --- Pending Loads Table ---
    st.subheader("🚛 Cargas en Arribo / Pendientes")
    
    pending_loads = disposal_service.get_pending_disposal_loads(current_site_id)
    
    if not pending_loads:
        st.info("No hay cargas pendientes de disposición en este sitio.")
        return

    # Prepare Data for Display
    table_data = []
    for load in pending_loads:
        # Resolve Names
        if load.origin_facility_id:
            fac = location_service.get_facility_by_id(load.origin_facility_id)
            origin = fac.name if fac else f"Fac-{load.origin_facility_id}"
        elif load.origin_treatment_plant_id:
            plant = treatment_plant_service.get_plant_by_id(load.origin_treatment_plant_id)
            origin = plant.name if plant else f"Plant-{load.origin_treatment_plant_id}"
        else:
            origin = "Desconocido"
            
        driver = transport_service.get_driver_by_id(load.driver_id)
        driver_name = driver.name if driver else "N/A"
        
        table_data.append({
            "ID": load.id,
            "Guía": load.guide_number or "N/A",
            "Origen": origin,
            "Chofer": driver_name,
            "Estado": load.status,
            "Hora Arribo": load.arrival_time.strftime("%H:%M") if load.arrival_time else "N/A"
        })
        
    df = pd.DataFrame(table_data)
    
    # Interactive Table
    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="disposal_grid"
    )
    
    if selection.selection.rows:
        selected_index = selection.selection.rows[0]
        selected_load_id = df.iloc[selected_index]["ID"]
        selected_load_data = df.iloc[selected_index]
        
        st.divider()
        st.header(f"Validación de Descarga - Carga #{selected_load_id}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🗺️ Validación Geoespacial")
            
            # Map Logic
            # Default to site coordinates. If site has no coords, default to Santiago.
            # Assuming Site model has latitude/longitude or similar. 
            # If not, we'll mock it for the view if the model doesn't support it yet.
            
            # Let's check if Site has lat/lon. If not, we use a default.
            lat = getattr(current_site, 'latitude', -33.4489)
            lon = getattr(current_site, 'longitude', -70.6693)
            
            # Truck position (Simulated: slightly offset from site)
            truck_lat = lat + 0.001
            truck_lon = lon + 0.001
            
            view_state = pdk.ViewState(
                latitude=lat,
                longitude=lon,
                zoom=14,
                pitch=0,
            )
            
            # Layers
            site_layer = pdk.Layer(
                "ScatterplotLayer",
                data=[{"position": [lon, lat], "color": [0, 255, 0, 160], "radius": 100}],
                get_position="position",
                get_color="color",
                get_radius="radius",
                pickable=True,
                auto_highlight=True,
            )
            
            truck_layer = pdk.Layer(
                "ScatterplotLayer",
                data=[{"position": [truck_lon, truck_lat], "color": [255, 0, 0, 160], "radius": 50}],
                get_position="position",
                get_color="color",
                get_radius="radius",
                pickable=True,
                auto_highlight=True,
            )

            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=view_state,
                layers=[site_layer, truck_layer],
                tooltip={"text": "Punto de Interés"}
            ))
            
            st.caption("🟢 Sitio Autorizado | 🔴 Ubicación Camión (Simulada)")

        with col2:
            st.markdown("### ✅ Checklist Normativo (EPA 503)")
            
            with st.form("compliance_form"):
                st.info(f"Conductor: {selected_load_data['Chofer']} | Guía: {selected_load_data['Guía']}")
                
                check_buffers = st.checkbox("Se respetan zonas de exclusión (buffers)")
                check_weather = st.checkbox("Condiciones climáticas aptas (sin lluvia)")
                check_soil = st.checkbox("Suelo preparado / Método de incorporación verificado")
                
                # Coordinates for the record (using the simulated truck pos)
                coords_str = f"{truck_lat},{truck_lon}"
                
                submitted = st.form_submit_button("CONFIRMAR DISPOSICIÓN FINAL", type="primary")
                
                if submitted:
                    if check_buffers and check_weather and check_soil:
                        try:
                            disposal_service.execute_disposal(
                                load_id=int(selected_load_id),
                                coordinates=coords_str
                            )
                            st.success("✅ Disposición registrada exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar: {str(e)}")
                    else:
                        st.error("⛔ Debe validar todos los puntos normativos antes de confirmar.")

if __name__ == "__main__":
    # Standalone execution for testing
    st.set_page_config(page_title="Disposal View Test", layout="wide")
    
    # Mocking DB Manager for standalone run if needed, 
    # but better to rely on actual DB if available in the environment.
    # If this script is run directly, it will try to connect to the DB.
    try:
        disposal_page()
    except Exception as e:
        st.error(f"Application Error: {e}")

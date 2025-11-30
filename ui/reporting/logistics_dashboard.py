import streamlit as st
import pandas as pd
from services.reporting.reporting_service import ReportingService

def logistics_dashboard_page():
    st.header("Torre de Control Logística")
    
    service = ReportingService()
    df = service.get_fleet_monitoring()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    total_in_transit = len(df)
    # Define delay threshold (e.g., 4 hours)
    DELAY_THRESHOLD_HOURS = 4.0
    
    delayed_trucks = len(df[df['hours_elapsed'] > DELAY_THRESHOLD_HOURS]) if not df.empty else 0
    on_time_trucks = total_in_transit - delayed_trucks
    
    col1.metric("Camiones en Ruta", total_in_transit)
    col2.metric("Atrasados (>4h)", delayed_trucks, delta=-delayed_trucks, delta_color="inverse")
    col3.metric("En Tiempo", on_time_trucks)
    
    st.divider()
    
    if df.empty:
        st.info("No hay camiones en tránsito actualmente.")
        return

    # Prepare DataFrame for display
    display_cols = {
        'load_id': 'ID Carga',
        'license_plate': 'Patente',
        'driver_name': 'Conductor',
        'origin_facility_id': 'Origen', # Using ID as name might not be in view yet, let's check view
        'facility_name': 'Planta Origen',
        'site_name': 'Destino',
        'dispatch_time': 'Hora Salida',
        'hours_elapsed': 'Horas en Ruta'
    }
    
    # Filter available columns
    available_cols = [c for c in display_cols.keys() if c in df.columns]
    df_display = df[available_cols].rename(columns=display_cols)
    
    # Apply Conditional Formatting
    # We need to apply style to the dataframe before rendering with st.dataframe if we want specific cell coloring,
    # BUT st.dataframe supports pandas Styler objects.
    
    def highlight_delayed(row):
        # If 'Horas en Ruta' > 4, color red
        if row['Horas en Ruta'] > DELAY_THRESHOLD_HOURS:
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    st.subheader("Monitoreo de Flota en Tiempo Real")
    
    # Create Styler
    styler = df_display.style.apply(highlight_delayed, axis=1)
    
    # Format columns
    styler.format({
        'Horas en Ruta': "{:.1f} h",
        'Hora Salida': lambda t: t.strftime("%H:%M") if pd.notnull(t) else ""
    })
    
    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True
    )
    
    # Auto-refresh hint
    st.caption("Esta vista se actualiza automáticamente cada 60 segundos (simulado).")

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.reporting.reporting_service import ReportingService

def client_portal_page():
    st.header("Portal de Cliente")
    st.markdown("Bienvenido. Aquí puede revisar la trazabilidad completa de sus residuos.")

    # Initialize Service
    service = ReportingService()

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        # Date Range Picker
        today = datetime.now()
        start_date = today - timedelta(days=30)
        date_range = st.date_input(
            "Rango de Fechas",
            value=(start_date, today),
            format="DD/MM/YYYY"
        )
    
    # Fetch Data
    # In a real app, we would filter by the logged-in user's client_id
    # For this demo, we'll fetch all and maybe filter by a selected client if admin, 
    # or just show everything for the "Client View" demo.
    
    # Handle date range tuple
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df = service.get_client_report(date_range=date_range)
    else:
        st.info("Seleccione un rango de fechas válido.")
        return

    if df.empty:
        st.warning("No se encontraron registros para este período.")
        return

    # Data Cleaning for Presentation
    # Select and Rename Columns for the Client
    display_cols = {
        'ticket_number': 'Ticket',
        'guide_number': 'Guía Despacho',
        'dispatch_time': 'Fecha Despacho',
        'site_name': 'Destino Final',
        'weight_net': 'Kilos Netos',
        'status': 'Estado',
        'batch_code': 'Lote Origen',
        'license_plate': 'Patente Camión'
    }
    
    # Filter columns that exist in the dataframe
    available_cols = [c for c in display_cols.keys() if c in df.columns]
    df_display = df[available_cols].rename(columns=display_cols)
    
    # Add a simulated "Certificate" link
    # We'll just create a string column that looks like a filename
    df_display['Certificado'] = df_display['Ticket'].apply(lambda x: f"CERT-{x}.pdf" if x else "Pendiente")

    # Display Configuration
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fecha Despacho": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Kilos Netos": st.column_config.NumberColumn(format="%.0f kg"),
            "Certificado": st.column_config.LinkColumn(
                "Certificado Digital",
                display_text="Descargar PDF",
                help="Haga clic para descargar el certificado de disposición final"
            )
        }
    )

    # Download Button for Excel
    st.download_button(
        label="Descargar Reporte Excel",
        data=df_display.to_csv(index=False).encode('utf-8'),
        file_name='reporte_trazabilidad.csv',
        mime='text/csv'
    )

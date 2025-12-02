import streamlit as st
import pandas as pd
from container import get_container
from domain.logistics.entities.load_status import LoadStatus

def logistics_dashboard_page(reporting_service):
    st.header("🚛 Torre de Control Logística")
    st.markdown("**Monitoreo en Tiempo Real** - Datos reales del sistema")
    
    service = reporting_service
    df = service.get_fleet_monitoring()
    
    # === METRICS SECTION ===
    st.markdown("### 📊 Resumen Operacional")
    
    if df.empty:
        st.info("✅ Sin camiones en circuito. Todos los viajes han sido completados.")
        return
    
    # Separate metrics by status using enum
    df_dispatched = df[df['status'] == LoadStatus.EN_ROUTE_DESTINATION.value]
    df_arrived = df[df['status'] == LoadStatus.AT_DESTINATION.value]
    
    # Define delay threshold (e.g., 4 hours)
    DELAY_THRESHOLD_HOURS = 4.0
    WAITING_ALERT_HOURS = 2.0  # Alert if waiting more than 2 hours
    
    # Calculate delayed trucks (only for Dispatched)
    delayed_trucks = len(df_dispatched[df_dispatched['hours_elapsed'] > DELAY_THRESHOLD_HOURS])
    
    # Calculate trucks with long waiting time
    long_wait = len(df_arrived[df_arrived['waiting_time'] > WAITING_ALERT_HOURS])
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "🚚 En Ruta", 
        len(df_dispatched),
        help="Camiones despachados en tránsito hacia el sitio"
    )
    col2.metric(
        "⏰ Atrasados (>4h)", 
        delayed_trucks,
        delta=-delayed_trucks if delayed_trucks > 0 else None,
        delta_color="inverse",
        help="Camiones en ruta con más de 4 horas de viaje"
    )
    col3.metric(
        "⏸️ En Cola / Espera", 
        len(df_arrived),
        help="Camiones que llegaron al sitio esperando descarga"
    )
    col4.metric(
        "⚠️ Espera Larga (>2h)", 
        long_wait,
        delta=-long_wait if long_wait > 0 else None,
        delta_color="inverse",
        help="Camiones esperando más de 2 horas en el sitio"
    )
    
    st.divider()
    
    # === DETAILED TABLES ===
    tab1, tab2 = st.tabs(["🚛 En Ruta (Dispatched)", "⏸️ En Cola (Arrived)"])
    
    # TAB 1: DISPATCHED (En Ruta)
    with tab1:
        st.subheader("Camiones en Tránsito")
        
        if df_dispatched.empty:
            st.info("No hay camiones en ruta actualmente.")
        else:
            # Prepare display DataFrame
            display_cols_dispatched = ['load_id', 'license_plate', 'driver_name', 
                                       'facility_name', 'site_name', 'dispatch_time', 
                                       'hours_elapsed', 'weight_net', 'ticket_number']
            
            available_cols = [c for c in display_cols_dispatched if c in df_dispatched.columns]
            df_display = df_dispatched[available_cols].copy()
            
            # Rename for better presentation
            df_display = df_display.rename(columns={
                'load_id': 'ID',
                'license_plate': 'Patente',
                'driver_name': 'Conductor',
                'facility_name': 'Origen',
                'site_name': 'Destino',
                'dispatch_time': 'Hora Salida',
                'hours_elapsed': 'Tiempo Viaje (h)',
                'weight_net': 'Peso Neto (kg)',
                'ticket_number': 'Ticket'
            })
            
            # Apply conditional formatting
            def highlight_delayed(row):
                if 'Tiempo Viaje (h)' in row and row['Tiempo Viaje (h)'] > DELAY_THRESHOLD_HOURS:
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            
            styler = df_display.style.apply(highlight_delayed, axis=1)
            styler.format({
                'Tiempo Viaje (h)': "{:.1f}",
                'Peso Neto (kg)': "{:,.0f}",
                'Hora Salida': lambda t: t.strftime("%d/%m %H:%M") if pd.notnull(t) else "N/A"
            })
            
            st.dataframe(styler, use_container_width=True, hide_index=True)
            
            # Alert for delayed trucks
            if delayed_trucks > 0:
                st.warning(f"⚠️ {delayed_trucks} camión(es) con más de {DELAY_THRESHOLD_HOURS}h en ruta. Verificar estado.")
    
    # TAB 2: ARRIVED (En Cola)
    with tab2:
        st.subheader("Camiones Esperando Descarga")
        
        if df_arrived.empty:
            st.info("No hay camiones en cola. Todos los arribados han sido descargados.")
        else:
            # Prepare display DataFrame
            display_cols_arrived = ['load_id', 'license_plate', 'driver_name',
                                   'site_name', 'arrival_time', 'hours_elapsed',
                                   'waiting_time', 'weight_arrival', 'ticket_number']
            
            available_cols = [c for c in display_cols_arrived if c in df_arrived.columns]
            df_display_arrived = df_arrived[available_cols].copy()
            
            # Rename for better presentation
            df_display_arrived = df_display_arrived.rename(columns={
                'load_id': 'ID',
                'license_plate': 'Patente',
                'driver_name': 'Conductor',
                'site_name': 'Sitio',
                'arrival_time': 'Hora Llegada',
                'hours_elapsed': 'Duración Viaje (h)',
                'waiting_time': 'Tiempo Espera (h)',
                'weight_arrival': 'Peso Báscula (kg)',
                'ticket_number': 'Ticket'
            })
            
            # Apply conditional formatting for long waits
            def highlight_waiting(row):
                if 'Tiempo Espera (h)' in row and row['Tiempo Espera (h)'] > WAITING_ALERT_HOURS:
                    return ['background-color: #fff3cd'] * len(row)  # Yellow warning
                return [''] * len(row)
            
            styler_arrived = df_display_arrived.style.apply(highlight_waiting, axis=1)
            styler_arrived.format({
                'Duración Viaje (h)': "{:.1f}",
                'Tiempo Espera (h)': "{:.1f}",
                'Peso Báscula (kg)': "{:,.0f}",
                'Hora Llegada': lambda t: t.strftime("%d/%m %H:%M") if pd.notnull(t) else "N/A"
            })
            
            st.dataframe(styler_arrived, use_container_width=True, hide_index=True)
            
            # Alert for long waits
            if long_wait > 0:
                st.warning(f"⚠️ {long_wait} camión(es) esperando más de {WAITING_ALERT_HOURS}h. Priorizar descarga.")
    
    st.divider()
    st.caption("💡 Datos actualizados en tiempo real desde la base de datos. Refresque la página para actualizar.")

import streamlit as st
import pandas as pd
from container import get_container
from domain.logistics.entities.load_status import LoadStatus
from ui.presenters.logistics_presenter import LogisticsPresenter

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
    
    # Separate by status using enum
    df_dispatched = df[df['status'] == LoadStatus.EN_ROUTE_DESTINATION.value]
    df_arrived = df[df['status'] == LoadStatus.AT_DESTINATION.value]
    
    # Usar Presenter para calcular métricas
    metrics = LogisticsPresenter.calculate_fleet_metrics(df_dispatched, df_arrived)
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "🚚 En Ruta", 
        metrics.en_ruta,
        help="Camiones despachados en tránsito hacia el sitio"
    )
    col2.metric(
        "⏰ Atrasados (>4h)", 
        metrics.atrasados,
        delta=-metrics.atrasados if metrics.atrasados > 0 else None,
        delta_color="inverse",
        help="Camiones en ruta con más de 4 horas de viaje"
    )
    col3.metric(
        "⏸️ En Cola / Espera", 
        metrics.en_cola,
        help="Camiones que llegaron al sitio esperando descarga"
    )
    col4.metric(
        "⚠️ Espera Larga (>2h)", 
        metrics.espera_larga,
        delta=-metrics.espera_larga if metrics.espera_larga > 0 else None,
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
            # Usar Presenter para formatear tabla
            df_display = LogisticsPresenter.format_dispatched_table(df_dispatched)
            
            # Aplicar estilo condicional
            styler = df_display.style.apply(LogisticsPresenter.get_delay_highlighter(), axis=1)
            
            # Formatear columnas numéricas
            format_dict = LogisticsPresenter.get_format_dict()
            available_formats = {k: v for k, v in format_dict.items() if k in df_display.columns}
            
            # Formatear fecha si existe
            if 'Hora Salida' in df_display.columns:
                styler.format({
                    **available_formats,
                    'Hora Salida': lambda t: t.strftime("%d/%m %H:%M") if pd.notnull(t) else "N/A"
                })
            else:
                styler.format(available_formats)
            
            st.dataframe(styler, width="stretch", hide_index=True)
            
            # Alert for delayed trucks
            if metrics.atrasados > 0:
                st.warning(f"⚠️ {metrics.atrasados} camión(es) con más de {LogisticsPresenter.DELAY_THRESHOLD_HOURS}h en ruta. Verificar estado.")
    
    # TAB 2: ARRIVED (En Cola)
    with tab2:
        st.subheader("Camiones Esperando Descarga")
        
        if df_arrived.empty:
            st.info("No hay camiones en cola. Todos los arribados han sido descargados.")
        else:
            # Usar Presenter para formatear tabla
            df_display_arrived = LogisticsPresenter.format_arrived_table(df_arrived)
            
            # Aplicar estilo condicional
            styler_arrived = df_display_arrived.style.apply(LogisticsPresenter.get_waiting_highlighter(), axis=1)
            
            # Formatear columnas
            format_dict = LogisticsPresenter.get_format_dict()
            available_formats = {k: v for k, v in format_dict.items() if k in df_display_arrived.columns}
            
            if 'Hora Llegada' in df_display_arrived.columns:
                styler_arrived.format({
                    **available_formats,
                    'Hora Llegada': lambda t: t.strftime("%d/%m %H:%M") if pd.notnull(t) else "N/A"
                })
            else:
                styler_arrived.format(available_formats)
            
            st.dataframe(styler_arrived, width="stretch", hide_index=True)
            
            # Alert for long waits
            if metrics.espera_larga > 0:
                st.warning(f"⚠️ {metrics.espera_larga} camión(es) esperando más de {LogisticsPresenter.WAITING_ALERT_HOURS}h. Priorizar descarga.")
    
    st.divider()
    st.caption("💡 Datos actualizados en tiempo real desde la base de datos. Refresque la página para actualizar.")

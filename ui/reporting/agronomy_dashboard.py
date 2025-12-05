"""
Agronomy Dashboard - Drill-down agronómico con visualización de parcelas

Este dashboard permite analizar el estado de aplicación de nitrógeno
por sitio y parcela con soporte de selección interactiva.
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import Optional, Any


def agronomy_dashboard_page(reporting_service, location_service, agronomy_service: Optional[Any] = None):
    """
    Dashboard agronómico con drill-down por parcela.
    
    Args:
        reporting_service: ReportingService para estadísticas agregadas
        location_service: LocationService para obtener sitios
        agronomy_service: AgronomyDomainService para historial de aplicaciones (opcional)
    """
    st.header("Drill-Down Agronómico")
    
    service = reporting_service
    
    # Select Site (Master Filter)
    sites_list = location_service.get_all_sites()
    if not sites_list:
        st.warning("No hay sitios registrados.")
        return

    # Convert Site entities to dictionaries for DataFrame
    sites = pd.DataFrame([{
        'id': s.id,
        'name': s.name,
        'owner_name': getattr(s, 'owner_name', ''),
        'region': getattr(s, 'region', ''),
        'is_active': getattr(s, 'is_active', True)
    } for s in sites_list])
        
    selected_site_name = st.selectbox("Seleccionar Campo/Sitio", sites['name'])
    selected_site_id = sites[sites['name'] == selected_site_name]['id'].iloc[0]
    
    st.divider()
    
    # Layout: Two Columns
    col_master, col_detail = st.columns([1, 1])
    
    with col_master:
        st.subheader("Estado de Parcelas")
        df_plots = service.get_site_agronomy_stats(selected_site_id)
        
        if df_plots.empty:
            st.info("Este sitio no tiene parcelas configuradas.")
        else:
            # Configure Grid with Selection
            event = st.dataframe(
                df_plots,
                width="stretch",
                hide_index=True,
                column_config={
                    "name": "Parcela",
                    "usage_percent": st.column_config.ProgressColumn(
                        "Uso de N",
                        help="Porcentaje de Nitrógeno aplicado vs Capacidad Máxima",
                        format="%.0f%%",
                        min_value=0,
                        max_value=1,
                    ),
                    "current_n": st.column_config.NumberColumn("N Aplicado (kg)", format="%.1f"),
                    "max_n": st.column_config.NumberColumn("Capacidad (kg)", format="%.1f")
                },
                selection_mode="single-row",
                on_select="rerun"
            )
            
            # Get Selection
            selected_indices = event.selection.get("rows", [])
            
    with col_detail:
        if not df_plots.empty and selected_indices:
            selected_idx = selected_indices[0]
            selected_plot = df_plots.iloc[selected_idx]
            plot_id = selected_plot['id']
            plot_name = selected_plot['name']
            
            st.subheader(f"Detalle: {plot_name}")
            
            # Fetch history using service (not raw SQL in UI)
            df_history = _get_plot_history(agronomy_service, int(plot_id))
                
            if not df_history.empty:
                # Chart
                chart = alt.Chart(df_history).mark_bar().encode(
                    x='application_date:T',
                    y='nitrogen_load_applied:Q',
                    tooltip=['application_date', 'nitrogen_load_applied']
                ).properties(title="Aplicación de Nitrógeno por Fecha")
                
                st.altair_chart(chart, width="stretch")
                
                st.caption("Historial de Aplicaciones")
                st.dataframe(df_history, width="stretch", hide_index=True)
            else:
                st.info("No hay aplicaciones registradas para esta parcela.")
                
        elif df_plots.empty:
            pass
        else:
            st.info("Seleccione una parcela a la izquierda para ver detalles.")


def _get_plot_history(agronomy_service: Optional[Any], plot_id: int) -> pd.DataFrame:
    """
    Obtiene el historial de aplicaciones de una parcela.
    
    Usa el servicio de agronomía si está disponible, de lo contrario
    retorna un DataFrame vacío con las columnas esperadas.
    
    Args:
        agronomy_service: AgronomyDomainService (opcional)
        plot_id: ID de la parcela
        
    Returns:
        DataFrame con application_date, nitrogen_load_applied, total_tonnage_applied
    """
    if agronomy_service and hasattr(agronomy_service, 'get_plot_application_history'):
        try:
            history_data = agronomy_service.get_plot_application_history(plot_id)
            if history_data:
                return pd.DataFrame(history_data)
        except Exception as e:
            st.warning(f"Error al obtener historial: {e}")
    
    # Return empty DataFrame with expected columns
    return pd.DataFrame(columns=['application_date', 'nitrogen_load_applied', 'total_tonnage_applied'])

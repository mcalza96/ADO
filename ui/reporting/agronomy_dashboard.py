import streamlit as st
import pandas as pd
import altair as alt
from database.db_manager import DatabaseManager

def agronomy_dashboard_page(reporting_service, location_service):
    st.header("Drill-Down Agronómico")
    
    service = reporting_service
    
    # Select Site (Master Filter)
    # We need to list sites first.
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
                use_container_width=True,
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
                on_select="rerun" # Rerun to update the detail view
            )
            
            # Get Selection
            # st.dataframe with selection returns a dict with 'rows' indices
            selected_indices = event.selection.get("rows", [])
            
    with col_detail:
        if not df_plots.empty and selected_indices:
            selected_idx = selected_indices[0]
            selected_plot = df_plots.iloc[selected_idx]
            plot_id = selected_plot['id']
            plot_name = selected_plot['name']
            
            st.subheader(f"Detalle: {plot_name}")
            
            # Fetch history for this plot
            # We can use a direct query here or add a method to service.
            # For speed, let's add a quick query here or reuse service if possible.
            # Service doesn't have 'get_plot_history', so let's do a quick query via DB Manager for now
            # or extend service. Let's extend service via a direct call pattern for now to keep it cleanish.
            
            query_history = """
                SELECT application_date, nitrogen_load_applied, total_tonnage_applied
                FROM applications
                WHERE plot_id = ?
                ORDER BY application_date DESC
            """
            with DatabaseManager() as conn:
                df_history = pd.read_sql_query(query_history, conn, params=(int(plot_id),))
                
            if not df_history.empty:
                # Chart
                chart = alt.Chart(df_history).mark_bar().encode(
                    x='application_date:T',
                    y='nitrogen_load_applied:Q',
                    tooltip=['application_date', 'nitrogen_load_applied']
                ).properties(title="Aplicación de Nitrógeno por Fecha")
                
                st.altair_chart(chart, use_container_width=True)
                
                st.caption("Historial de Aplicaciones")
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("No hay aplicaciones registradas para esta parcela.")
                
        elif df_plots.empty:
            pass
        else:
            st.info("Seleccione una parcela a la izquierda para ver detalles.")

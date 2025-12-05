import streamlit as st
from domain.shared.entities.location import Site, Plot
from ui.state import AppState
from ui.constants import Region, DefaultCoordinates


def render(location_service):
    """
    Vista jerárquica Master-Detail para Sites (Predios) y Plots (Parcelas).
    
    Args:
        location_service: LocationService instance for data access
    """
    st.header("🌾 Gestión de Predios y Parcelas")
    
    # Initialize session state using AppState constants
    AppState.init_if_missing(AppState.SELECTED_SITE_ID, None)
    AppState.init_if_missing(AppState.PLOT_EDIT_ID, None)
    
    # Create 2-column layout
    col_list, col_detail = st.columns([1, 2])
    
    # LEFT COLUMN: Site List
    with col_list:
        st.subheader("Predios")
        
        # Add New Site Button
        if st.button("➕ Nuevo Predio", width="stretch"):
            AppState.set(AppState.SELECTED_SITE_ID, 'NEW')
        
        st.divider()
        
        # List existing sites
        sites = location_service.get_all_sites(active_only=True)
        
        if sites:
            for site in sites:
                is_selected = AppState.get(AppState.SELECTED_SITE_ID) == site.id
                button_type = "primary" if is_selected else "secondary"
                
                if st.button(
                    f"📍 {site.name}",
                    key=f"site_{site.id}",
                    width="stretch",
                    type=button_type
                ):
                    AppState.set(AppState.SELECTED_SITE_ID, site.id)
                    AppState.set(AppState.PLOT_EDIT_ID, None)
                    st.rerun()
        else:
            st.info("No hay predios registrados")
    
    # RIGHT COLUMN: Site Details + Plots
    with col_detail:
        selected_site_id = AppState.get(AppState.SELECTED_SITE_ID)
        
        if selected_site_id is None:
            st.info("👈 Seleccione un predio de la lista o cree uno nuevo")
        
        elif selected_site_id == 'NEW':
            # Create New Site Form
            st.subheader("Nuevo Predio")
            
            with st.form("new_site_form"):
                name = st.text_input("Nombre del Predio *", placeholder="ej. Fundo Los Olivos")
                owner = st.text_input("Propietario / Agricultor", placeholder="ej. Juan Pérez")
                region = st.selectbox("Región", Region.get_list())
                address = st.text_input("Dirección / Referencia", placeholder="ej. Camino a Melipilla km 45")
                
                col1, col2 = st.columns(2)
                with col1:
                    latitude = st.number_input("Latitud", format="%.6f", value=DefaultCoordinates.LATITUDE)
                with col2:
                    longitude = st.number_input("Longitud", format="%.6f", value=DefaultCoordinates.LONGITUDE)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 Guardar Predio", width="stretch")
                with col_cancel:
                    cancelled = st.form_submit_button("❌ Cancelar", width="stretch")
                
                if submitted:
                    if not name:
                        st.error("⚠️ El nombre del predio es obligatorio")
                    else:
                        try:
                            site = Site(
                                id=None,
                                name=name,
                                owner_name=owner,
                                region=region,
                                address=address,
                                latitude=latitude,
                                longitude=longitude
                            )
                            created_site = location_service.create_site(site)
                            st.success(f"✅ Predio '{name}' creado exitosamente")
                            AppState.set(AppState.SELECTED_SITE_ID, created_site.id)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear predio: {e}")
                
                if cancelled:
                    AppState.set(AppState.SELECTED_SITE_ID, None)
                    st.rerun()
        
        else:
            # Edit Existing Site
            site = location_service.get_site(selected_site_id)
            
            if not site:
                st.error("Predio no encontrado")
                AppState.set(AppState.SELECTED_SITE_ID, None)
                st.rerun()
                return
            
            st.subheader(f"Predio: {site.name}")
            
            # Site Edit Form
            with st.expander("✏️ Editar Datos del Predio"):
                with st.form("edit_site_form"):
                    name = st.text_input("Nombre del Predio *", value=site.name)
                    owner = st.text_input("Propietario", value=site.owner_name or "")
                    region = st.selectbox(
                        "Región",
                        Region.get_list(),
                        index=Region.get_index(site.region)
                    )
                    address = st.text_input("Dirección", value=site.address or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        latitude = st.number_input("Latitud", format="%.6f", value=site.latitude or DefaultCoordinates.LATITUDE)
                    with col2:
                        longitude = st.number_input("Longitud", format="%.6f", value=site.longitude or DefaultCoordinates.LONGITUDE)
                    
                    if st.form_submit_button("💾 Actualizar Predio"):
                        try:
                            site.name = name
                            site.owner_name = owner
                            site.region = region
                            site.address = address
                            site.latitude = latitude
                            site.longitude = longitude
                            
                            location_service.update_site(site)
                            st.success("✅ Predio actualizado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al actualizar predio: {e}")
            
            st.divider()
            
            # Plots Section
            st.subheader("Parcelas / Sectores")
            
            plots = location_service.get_plots_by_site(selected_site_id)
            
            # Add/Edit Plot Form
            plot_edit_id = AppState.get(AppState.PLOT_EDIT_ID)
            
            if plot_edit_id == 'NEW' or plot_edit_id:
                if plot_edit_id == 'NEW':
                    st.write("**Nueva Parcela**")
                    plot = Plot(id=None, site_id=selected_site_id, name="", area_hectares=0.0)
                else:
                    plot = next((p for p in plots if p.id == plot_edit_id), None)
                    if not plot:
                        AppState.set(AppState.PLOT_EDIT_ID, None)
                        st.rerun()
                        return
                    st.write(f"**Editar Parcela: {plot.name}**")
                
                with st.form("plot_form"):
                    plot_name = st.text_input("Nombre de la Parcela *", value=plot.name, placeholder="ej. Sector Norte")
                    plot_area = st.number_input("Área (hectáreas)", min_value=0.0, step=0.1, value=plot.area_hectares or 0.0)
                    plot_geometry = st.text_area(
                        "Geometría WKT (opcional)",
                        value=plot.geometry_wkt or "",
                        placeholder="POLYGON((-70.5 -33.5, -70.5 -33.4, -70.4 -33.4, -70.4 -33.5, -70.5 -33.5))",
                        help="Formato Well-Known Text para polígonos. Debe comenzar con POLYGON o MULTIPOLYGON"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_plot = st.form_submit_button("💾 Guardar Parcela", width="stretch")
                    with col_cancel:
                        cancel_plot = st.form_submit_button("❌ Cancelar", width="stretch")
                    
                    if save_plot:
                        if not plot_name:
                            st.error("⚠️ El nombre de la parcela es obligatorio")
                        else:
                            try:
                                plot.name = plot_name
                                plot.area_hectares = plot_area
                                plot.geometry_wkt = plot_geometry if plot_geometry else None
                                
                                if plot.id is None:
                                    location_service.create_plot(plot)
                                    st.success(f"✅ Parcela '{plot_name}' creada exitosamente")
                                else:
                                    location_service.update_plot(plot)
                                    st.success(f"✅ Parcela '{plot_name}' actualizada exitosamente")
                                
                                AppState.set(AppState.PLOT_EDIT_ID, None)
                                st.rerun()
                            except ValueError as ve:
                                st.error(f"⚠️ Error de validación: {ve}")
                            except Exception as e:
                                st.error(f"❌ Error al guardar parcela: {e}")
                    
                    if cancel_plot:
                        AppState.set(AppState.PLOT_EDIT_ID, None)
                        st.rerun()
            else:
                # Show Add Plot button
                if st.button("➕ Nueva Parcela", width="stretch"):
                    AppState.set(AppState.PLOT_EDIT_ID, 'NEW')
                    st.rerun()
            
            st.divider()
            
            # Display Plots Table using st.dataframe with selection
            if plots:
                st.write(f"**Parcelas Registradas ({len(plots)})**")
                
                # Build DataFrame for display
                plots_data = [{
                    "id": p.id,
                    "Nombre": p.name,
                    "Área (ha)": f"{p.area_hectares or 0:.2f}",
                    "Geometría": "✓" if p.geometry_wkt else "—"
                } for p in plots]
                
                import pandas as pd
                df_plots = pd.DataFrame(plots_data)
                
                # Interactive table with selection
                event = st.dataframe(
                    df_plots,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "id": None,  # Hide ID column
                        "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                        "Área (ha)": st.column_config.TextColumn("Área (ha)", width="small"),
                        "Geometría": st.column_config.TextColumn("WKT", width="small")
                    },
                    selection_mode="single-row",
                    on_select="rerun"
                )
                
                # Handle selection for edit/delete actions
                selected_rows = event.selection.get("rows", [])
                if selected_rows:
                    selected_plot_id = plots_data[selected_rows[0]]["id"]
                    selected_plot = next((p for p in plots if p.id == selected_plot_id), None)
                    
                    if selected_plot:
                        st.caption(f"Parcela seleccionada: **{selected_plot.name}**")
                        col_edit, col_delete = st.columns(2)
                        
                        with col_edit:
                            if st.button("✏️ Editar Parcela", width="stretch"):
                                AppState.set(AppState.PLOT_EDIT_ID, selected_plot.id)
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️ Eliminar Parcela", width="stretch", type="secondary"):
                                try:
                                    location_service.delete_plot(selected_plot.id)
                                    st.success(f"✅ Parcela '{selected_plot.name}' eliminada")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
            else:
                st.info("No hay parcelas registradas para este predio")

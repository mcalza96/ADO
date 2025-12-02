import streamlit as st
from models.masters.location import Site, Plot


def render(location_service):
    """
    Vista jerárquica Master-Detail para Sites (Predios) y Plots (Parcelas).
    
    Args:
        location_service: LocationService instance for data access
    """
    st.header("🌾 Gestión de Predios y Parcelas")
    
    # Initialize session state
    if 'selected_site_id' not in st.session_state:
        st.session_state['selected_site_id'] = None
    if 'plot_edit_id' not in st.session_state:
        st.session_state['plot_edit_id'] = None
    
    # Create 2-column layout
    col_list, col_detail = st.columns([1, 2])
    
    # LEFT COLUMN: Site List
    with col_list:
        st.subheader("Predios")
        
        # Add New Site Button
        if st.button("➕ Nuevo Predio", use_container_width=True):
            st.session_state['selected_site_id'] = 'NEW'
        
        st.divider()
        
        # List existing sites
        sites = location_service.get_all_sites(active_only=True)
        
        if sites:
            for site in sites:
                is_selected = st.session_state['selected_site_id'] == site.id
                button_type = "primary" if is_selected else "secondary"
                
                if st.button(
                    f"📍 {site.name}",
                    key=f"site_{site.id}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state['selected_site_id'] = site.id
                    st.session_state['plot_edit_id'] = None
                    st.rerun()
        else:
            st.info("No hay predios registrados")
    
    # RIGHT COLUMN: Site Details + Plots
    with col_detail:
        selected_site_id = st.session_state['selected_site_id']
        
        if selected_site_id is None:
            st.info("👈 Seleccione un predio de la lista o cree uno nuevo")
        
        elif selected_site_id == 'NEW':
            # Create New Site Form
            st.subheader("Nuevo Predio")
            
            with st.form("new_site_form"):
                name = st.text_input("Nombre del Predio *", placeholder="ej. Fundo Los Olivos")
                owner = st.text_input("Propietario / Agricultor", placeholder="ej. Juan Pérez")
                region = st.selectbox(
                    "Región",
                    ["Metropolitana", "Valparaíso", "O'Higgins", "Maule", "Biobío", "Araucanía", "Los Lagos"]
                )
                address = st.text_input("Dirección / Referencia", placeholder="ej. Camino a Melipilla km 45")
                
                col1, col2 = st.columns(2)
                with col1:
                    latitude = st.number_input("Latitud", format="%.6f", value=-33.4489)
                with col2:
                    longitude = st.number_input("Longitud", format="%.6f", value=-70.6693)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 Guardar Predio", use_container_width=True)
                with col_cancel:
                    cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
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
                            st.session_state['selected_site_id'] = created_site.id
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al crear predio: {e}")
                
                if cancelled:
                    st.session_state['selected_site_id'] = None
                    st.rerun()
        
        else:
            # Edit Existing Site
            site = location_service.get_site(selected_site_id)
            
            if not site:
                st.error("Predio no encontrado")
                st.session_state['selected_site_id'] = None
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
                        ["Metropolitana", "Valparaíso", "O'Higgins", "Maule", "Biobío", "Araucanía", "Los Lagos"],
                        index=0 if not site.region else ["Metropolitana", "Valparaíso", "O'Higgins", "Maule", "Biobío", "Araucanía", "Los Lagos"].index(site.region) if site.region in ["Metropolitana", "Valparaíso", "O'Higgins", "Maule", "Biobío", "Araucanía", "Los Lagos"] else 0
                    )
                    address = st.text_input("Dirección", value=site.address or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        latitude = st.number_input("Latitud", format="%.6f", value=site.latitude or -33.4489)
                    with col2:
                        longitude = st.number_input("Longitud", format="%.6f", value=site.longitude or -70.6693)
                    
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
            plot_edit_id = st.session_state.get('plot_edit_id')
            
            if plot_edit_id == 'NEW' or plot_edit_id:
                if plot_edit_id == 'NEW':
                    st.write("**Nueva Parcela**")
                    plot = Plot(id=None, site_id=selected_site_id, name="", area_acres=0.0)
                else:
                    plot = next((p for p in plots if p.id == plot_edit_id), None)
                    if not plot:
                        st.session_state['plot_edit_id'] = None
                        st.rerun()
                        return
                    st.write(f"**Editar Parcela: {plot.name}**")
                
                with st.form("plot_form"):
                    plot_name = st.text_input("Nombre de la Parcela *", value=plot.name, placeholder="ej. Sector Norte")
                    plot_area = st.number_input("Área (hectáreas)", min_value=0.0, step=0.1, value=plot.area_acres or 0.0)
                    plot_geometry = st.text_area(
                        "Geometría WKT (opcional)",
                        value=plot.geometry_wkt or "",
                        placeholder="POLYGON((-70.5 -33.5, -70.5 -33.4, -70.4 -33.4, -70.4 -33.5, -70.5 -33.5))",
                        help="Formato Well-Known Text para polígonos. Debe comenzar con POLYGON o MULTIPOLYGON"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_plot = st.form_submit_button("💾 Guardar Parcela", use_container_width=True)
                    with col_cancel:
                        cancel_plot = st.form_submit_button("❌ Cancelar", use_container_width=True)
                    
                    if save_plot:
                        if not plot_name:
                            st.error("⚠️ El nombre de la parcela es obligatorio")
                        else:
                            try:
                                plot.name = plot_name
                                plot.area_acres = plot_area
                                plot.geometry_wkt = plot_geometry if plot_geometry else None
                                
                                if plot.id is None:
                                    location_service.create_plot(plot)
                                    st.success(f"✅ Parcela '{plot_name}' creada exitosamente")
                                else:
                                    location_service.update_plot(plot)
                                    st.success(f"✅ Parcela '{plot_name}' actualizada exitosamente")
                                
                                st.session_state['plot_edit_id'] = None
                                st.rerun()
                            except ValueError as ve:
                                st.error(f"⚠️ Error de validación: {ve}")
                            except Exception as e:
                                st.error(f"❌ Error al guardar parcela: {e}")
                    
                    if cancel_plot:
                        st.session_state['plot_edit_id'] = None
                        st.rerun()
            else:
                # Show Add Plot button
                if st.button("➕ Nueva Parcela", use_container_width=True):
                    st.session_state['plot_edit_id'] = 'NEW'
                    st.rerun()
            
            st.divider()
            
            # Display Plots Table
            if plots:
                st.write(f"**Parcelas Registradas ({len(plots)})**")
                
                for plot in plots:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**{plot.name}**")
                            st.caption(f"Área: {plot.area_acres or 0:.2f} ha" + (f" | WKT: ✓" if plot.geometry_wkt else ""))
                        
                        with col2:
                            if st.button("✏️ Editar", key=f"edit_plot_{plot.id}"):
                                st.session_state['plot_edit_id'] = plot.id
                                st.rerun()
                        
                        with col3:
                            if st.button("🗑️ Eliminar", key=f"delete_plot_{plot.id}", type="secondary"):
                                try:
                                    location_service.delete_plot(plot.id)
                                    st.success(f"✅ Parcela '{plot.name}' eliminada")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                        
                        st.divider()
            else:
                st.info("No hay parcelas registradas para este predio")

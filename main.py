import streamlit as st
from ui.state import AppState
from ui.auth.login import login_page
from ui.config_view import config_page
from ui.requests_view import requests_page
from ui.planning_view import planning_page
from ui.inbox_view import inbox_page
from ui.disposal.operations import disposal_operations_page
from ui.treatment.operations import treatment_operations_page
from ui.operations.dashboard_view import dashboard_page

from ui.reporting.client_portal import client_portal_page
from ui.reporting.logistics_dashboard import logistics_dashboard_page
from ui.reporting.agronomy_dashboard import agronomy_dashboard_page
from ui.reporting.financial_portal import financial_portal_page

# Import Registry-based modules (auto-register their pages)
import ui.modules.logistics  # Auto-registers: Despacho, Recepción, Planificación, Tracking

# Page configuration
st.set_page_config(
    page_title="Biosolids ERP",
    page_icon="🚛",
    layout="wide"
)

import sqlite3
import os

from container import get_container

def main():
    # Initialize session state for user using AppState
    AppState.init_if_missing(AppState.USER, None)

    # Check if user is logged in
    if AppState.get(AppState.USER) is None:
        login_page()
    else:
        # Main App Layout
        user = AppState.get(AppState.USER)
        
        # Get Services Container (single source of truth)
        container = get_container()
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("Biosolids ERP")
            st.write(f"User: **{user.username}** ({user.role})")
            st.divider()
            
            # Nuevo Menú Simplificado
            menu_options = ["Mi Bandeja (Inbox)", "Dashboard", "Solicitudes", "Operaciones", "Reportes", "Configuración"]
            selection = st.radio("Navegación", menu_options)
            
            st.divider()
            
            if st.button("Logout"):
                AppState.clear(AppState.USER)
                st.rerun()

        # Router Principal - Usando container completo para eliminar prop drilling
        if selection == "Mi Bandeja (Inbox)":
            # Pasamos container y usuario (DI correcto)
            inbox_page(container=container, user_role=user.role, user_id=user.id)
            
        elif selection == "Dashboard":
            dashboard_page(container.dashboard_service)
        
        elif selection == "Solicitudes":
            # Client pickup requests - pasamos container completo
            requests_page(container=container)
            
        elif selection == "Operaciones":
            # Sub-navigation for Operations
            ops_menu = st.sidebar.radio(
                "Módulos Operacionales",
                ["🚛 Logística (Despacho)", "🏭 Tratamiento (Planta)", "🌾 Disposición Final (Agro)"]
            )
            
            if ops_menu == "🚛 Logística (Despacho)":
                # Use Registry Pattern for Logistics
                from ui.registry import UIRegistry, MenuBuilder
                
                # Get logistics menu items
                all_items = UIRegistry.get_all_items()
                logistics_items = all_items.get("Operaciones Logísticas", [])
                
                if logistics_items:
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("### 📋 Operaciones Disponibles")
                    
                    # Create menu from registered items
                    menu_options = {f"{item.icon} {item.title}": item for item in sorted(logistics_items, key=lambda x: x.order)}
                    selected_option = st.sidebar.radio("Seleccione operación:", list(menu_options.keys()), label_visibility="collapsed")
                    
                    # Render selected page
                    if selected_option:
                        selected_item = menu_options[selected_option]
                        try:
                            # Call the page function with container
                            selected_item.page_func(container)
                        except Exception as e:
                            st.error(f"Error al cargar la página: {str(e)}")
                            st.exception(e)
                else:
                    st.warning("No hay operaciones de logística registradas")
                    st.info("Verifica que el módulo ui.modules.logistics esté importado correctamente")
                
            elif ops_menu == "🏭 Tratamiento (Planta)":
                treatment_operations_page(container)
                
            elif ops_menu == "🌾 Disposición Final (Agro)":
                disposal_operations_page(container=container)
            
        elif selection == "Reportes":
            # Sub-navigation for Reportes
            report_menu = st.sidebar.radio(
                "Vistas de Inteligencia",
                ["Torre de Control (Logística)", "Drill-Down Agronómico", "Vista Cliente (Simulada)", "Estados de Pago"]
            )
            
            if report_menu == "Torre de Control (Logística)":
                logistics_dashboard_page(container.reporting_service)
            elif report_menu == "Drill-Down Agronómico":
                agronomy_dashboard_page(container.reporting_service, container.location_service, container.agronomy_service)
            elif report_menu == "Vista Cliente (Simulada)":
                client_portal_page(container.reporting_service)
            elif report_menu == "Estados de Pago":
                financial_portal_page(container)
                
        elif selection == "Configuración":
            config_page(container)

if __name__ == "__main__":
    main()

"""
Main Application Entry Point (Refactored with Registry Pattern)

This version uses the UI Registry pattern for dynamic menu generation.

Key Benefits:
- Adding new modules doesn't require changing this file
- Just import the module and it auto-registers
- Open/Closed Principle: open for extension, closed for modification
- RBAC-ready for future permission system

How to add a new module:
    1. Create ui/modules/your_module.py
    2. Import UIRegistry and create page functions
    3. Register pages using UIRegistry.register() or @auto_register decorator
    4. Import the module here (line ~80)
    5. That's it! Menu appears automatically
"""

import streamlit as st
import sqlite3
import os

# Page configuration
st.set_page_config(
    page_title="Biosolids ERP",
    page_icon="🚛",
    layout="wide"
)


def run_migrations():
    """
    Checks and applies critical database migrations.
    """
    db_path = "database/biosolids.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for requested_date in loads
            cursor.execute("PRAGMA table_info(loads)")
            columns = [info[1] for info in cursor.fetchall()]
            if "requested_date" not in columns:
                cursor.execute("ALTER TABLE loads ADD COLUMN requested_date DATETIME")
                conn.commit()
                print("Migration applied: Added requested_date to loads table.")
                
            conn.close()
        except Exception as e:
            print(f"Migration failed: {e}")


def main():
    """
    Main application entry point.
    
    This new version is much simpler:
    1. Check authentication
    2. Import modules (they auto-register)
    3. Use MenuBuilder to render menu and selected page
    """
    # Initialize session state for user
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Check if user is logged in
    if st.session_state['user'] is None:
        # Login page
        from ui.auth.login import login_page
        login_page()
    else:
        # ====================================================================
        # MODULE IMPORTS (Auto-Registration)
        # ====================================================================
        # Each module registers itself when imported
        # To add a new module, just import it here!
        
        # Import legacy pages (will be migrated to registry pattern)
        from ui.inbox_view import inbox_page
        from ui.operations.dashboard_view import dashboard_page
        from ui.reporting.client_portal import client_portal_page
        from ui.reporting.logistics_dashboard import logistics_dashboard_page
        from ui.reporting.agronomy_dashboard import agronomy_dashboard_page
        from ui.config_view import config_page
        
        # Import new registry-based modules (auto-register)
        import ui.modules.logistics  # 🚛 Logistics operations
        # import ui.modules.agronomy  # 🌱 Agronomy operations (create this next)
        # import ui.modules.treatment  # 🏭 Treatment operations (create this next)
        # import ui.modules.compliance  # ✅ Compliance module (future)
        # import ui.modules.community  # 👥 Community module (from Excel)
        
        # ====================================================================
        # CONTAINER AND USER
        # ====================================================================
        user = st.session_state['user']
        
        # Get Services from Container (new modular container)
        from config.dependencies import get_container
        container = get_container()
        
        # ====================================================================
        # MENU RENDERING (Dynamic from Registry)
        # ====================================================================
        from ui.registry import UIRegistry, MenuBuilder
        
        # Create menu builder
        menu_builder = MenuBuilder(container, user)
        
        # Render sidebar and get selected page
        selected_item = menu_builder.render_sidebar()
        
        # ====================================================================
        # PAGE ROUTING
        # ====================================================================
        
        # Check if selected item is from registry
        if selected_item is not None:
            # New registry-based page
            menu_builder.render_selected_page(selected_item)
        else:
            # Legacy routing (for pages not yet migrated to registry)
            # This section can be removed once all pages are migrated
            
            # Show legacy menu if no registry items selected
            with st.sidebar:
                st.divider()
                st.markdown("### 🔧 Legacy Menu")
                legacy_menu = st.radio(
                    "Old Navigation",
                    ["Mi Bandeja (Inbox)", "Dashboard", "Reportes", "Configuración"]
                )
            
            if legacy_menu == "Mi Bandeja (Inbox)":
                inbox_page(user_role=user.role, user_id=user.id)
                
            elif legacy_menu == "Dashboard":
                dashboard_page(container.dashboard_service)
                
            elif legacy_menu == "Reportes":
                # Sub-navigation for Reportes
                report_menu = st.sidebar.radio(
                    "Vistas de Inteligencia",
                    ["Torre de Control (Logística)", "Drill-Down Agronómico", "Vista Cliente (Simulada)"]
                )
                
                if report_menu == "Torre de Control (Logística)":
                    logistics_dashboard_page(container.reporting_service)
                elif report_menu == "Drill-Down Agronómico":
                    agronomy_dashboard_page(container.reporting_service, container.location_service)
                elif report_menu == "Vista Cliente (Simulada)":
                    client_portal_page(container.reporting_service)
                    
            elif legacy_menu == "Configuración":
                config_page(
                    client_service=container.client_service,
                    facility_service=container.facility_service,
                    contractor_service=container.contractor_service,
                    treatment_plant_service=container.treatment_plant_service,
                    container_service=container.container_service,
                    location_service=container.location_service,
                    driver_service=container.driver_service,
                    vehicle_service=container.vehicle_service,
                    auth_service=container.auth_service
                )


if __name__ == "__main__":
    run_migrations()
    main()

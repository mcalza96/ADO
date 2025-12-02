import streamlit as st
from ui.auth.login import login_page
from ui.config_view import config_page
from ui.requests_view import requests_page
from ui.planning_view import planning_page
from ui.operations.operations_view import operations_page
from ui.operations.dispatch_view import dispatch_view
from ui.operations.reception_view import reception_view
from ui.disposal.operations import disposal_operations_page
from ui.treatment.operations import treatment_operations_page
from ui.operations.dashboard_view import dashboard_page

from ui.reporting.client_portal import client_portal_page
from ui.reporting.logistics_dashboard import logistics_dashboard_page
from ui.reporting.agronomy_dashboard import agronomy_dashboard_page

# Page configuration
st.set_page_config(
    page_title="Biosolids ERP",
    page_icon="🚛",
    layout="wide"
)

import sqlite3
import os

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

from container import get_container

def main():
    # Initialize session state for user
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Check if user is logged in
    if st.session_state['user'] is None:
        login_page()
    else:
        # Main App Layout
        user = st.session_state['user']
        
        # Get Services from Container
        services = get_container()
        
        # Extract all services needed for different modules
        treatment_plant_service = services.treatment_plant_service
        client_service = services.client_service
        contractor_service = services.contractor_service
        container_service = services.container_service
        location_service = services.location_service
        driver_service = services.driver_service
        vehicle_service = services.vehicle_service
        auth_service = services.auth_service
        logistics_service = services.logistics_service
        dispatch_service = services.dispatch_service
        reporting_service = services.reporting_service
        treatment_service = services.treatment_service
        batch_service = services.batch_service
        treatment_reception_service = services.treatment_reception_service
        master_disposal_service = services.master_disposal_service
        disposal_service = services.disposal_service
        treatment_batch_service = services.treatment_batch_service
        dashboard_service = services.dashboard_service
        site_prep_service = services.site_prep_service
        reception_service = services.reception_service
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("Biosolids ERP")
            st.write(f"User: **{user.username}** ({user.role})")
            st.divider()
            
            # Main Module Selection
            module = st.selectbox(
                "Módulo",
                ["Dashboard", "Reportes", "Portal Clientes", "Transporte", "Disposición", "Tratamiento", "Configuración"]
            )
            
            st.divider()
            
            # Sub-navigation for Transporte
            sub_menu = None
            if module == "Transporte":
                sub_menu = st.radio(
                    "Gestión de Transporte",
                    ["Planificación", "Despacho", "Recepción", "Operaciones (Legacy)"]
                )
            
            # Sub-navigation for Reportes
            report_menu = None
            if module == "Reportes":
                report_menu = st.radio(
                    "Vistas de Inteligencia",
                    ["Torre de Control (Logística)", "Drill-Down Agronómico", "Vista Cliente (Simulada)"]
                )
            
            if st.button("Logout"):
                st.session_state['user'] = None
                st.rerun()

        # Main Content Area
        if module == "Dashboard":
            dashboard_page(dashboard_service)
            
        elif module == "Reportes":
            if report_menu == "Torre de Control (Logística)":
                logistics_dashboard_page(reporting_service)
            elif report_menu == "Drill-Down Agronómico":
                agronomy_dashboard_page(reporting_service, location_service)
            elif report_menu == "Vista Cliente (Simulada)":
                client_portal_page(reporting_service)

        elif module == "Portal Clientes":
            requests_page(client_service, location_service, logistics_service, treatment_plant_service)
            
        elif module == "Transporte":
            if sub_menu == "Planificación":
                planning_page(logistics_service, contractor_service, driver_service, vehicle_service, location_service, treatment_plant_service)
            elif sub_menu == "Despacho":
                dispatch_view(vehicle_service, dispatch_service, location_service, treatment_plant_service)
            elif sub_menu == "Recepción":
                reception_view(reception_service, treatment_plant_service)
            elif sub_menu == "Operaciones (Legacy)":
                operations_page(logistics_service, treatment_service, master_disposal_service, container_service)
                
        elif module == "Disposición":
            disposal_operations_page(disposal_service, location_service, driver_service, treatment_plant_service, site_prep_service)
            
        elif module == "Tratamiento":
            treatment_operations_page(treatment_plant_service, treatment_reception_service, batch_service, container_service, treatment_batch_service, logistics_service)
            
        elif module == "Configuración":
            config_page(
                client_service=client_service,
                contractor_service=contractor_service,
                treatment_plant_service=treatment_plant_service,
                container_service=container_service,
                location_service=location_service,
                driver_service=driver_service,
                vehicle_service=vehicle_service,
                auth_service=auth_service
            )

if __name__ == "__main__":
    run_migrations()
    main()

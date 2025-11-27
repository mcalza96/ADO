import streamlit as st
from ui.auth.login import login_page
from ui.config_view import config_page
from ui.requests_view import requests_page
from ui.planning_view import planning_page
from ui.operations.operations_view import operations_page
from ui.operations.dashboard_view import dashboard_page

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
        
        # Sidebar Navigation
        with st.sidebar:
            st.title("Biosolids ERP")
            st.write(f"User: **{user.username}** ({user.role})")
            st.divider()
            
            menu = st.radio(
                "Navegación",
                ["Dashboard", "Solicitudes", "Planificación", "Operaciones", "Configuración"]
            )
            
            st.divider()
            if st.button("Logout"):
                st.session_state['user'] = None
                st.rerun()

        # Main Content Area
        if menu == "Dashboard":
            dashboard_page()
        elif menu == "Solicitudes":
            requests_page()
        elif menu == "Planificación":
            planning_page()
        elif menu == "Operaciones":
            operations_page()
        elif menu == "Configuración":
            config_page()

if __name__ == "__main__":
    run_migrations()
    main()

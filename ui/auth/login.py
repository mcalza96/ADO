"""
Login Page - Autenticación de usuarios.

Refactorizado para:
- Usar AppState para manejo de session state
- Recibir auth_service como dependencia inyectada
"""

import streamlit as st
from ui.state import AppState


def login_page(auth_service=None):
    """
    Página de login.
    
    Args:
        auth_service: Servicio de autenticación. Si no se proporciona,
                     se obtiene del container (compatibilidad hacia atrás).
    """
    st.title("Biosolids ERP - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Obtener auth_service si no fue inyectado (compatibilidad)
            if auth_service is None:
                from container import get_container
                auth_service = get_container().auth_service
                
            user = auth_service.authenticate(username, password)
            
            if user:
                AppState.set(AppState.USER, user)
                st.success(f"Welcome {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

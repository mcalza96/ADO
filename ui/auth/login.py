import streamlit as st
from services.auth_service import AuthService
from database.db_manager import DatabaseManager

def login_page():
    st.title("Biosolids ERP - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            db = DatabaseManager()
            auth_service = AuthService(db)
            user = auth_service.authenticate(username, password)
            
            if user:
                st.session_state['user'] = user
                st.success(f"Welcome {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

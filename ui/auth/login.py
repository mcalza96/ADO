import streamlit as st
from container import get_container

def login_page():
    st.title("Biosolids ERP - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            services = get_container()
            user = services.auth_service.authenticate(username, password)
            
            if user:
                st.session_state['user'] = user
                st.success(f"Welcome {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

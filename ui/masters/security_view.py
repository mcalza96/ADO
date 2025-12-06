"""
Security View - Gestión de Usuarios y Seguridad

Extraído de config_view.py para mejor separación de responsabilidades.
"""

import streamlit as st
from typing import List, Optional
from ui.presenters.status_presenter import StatusPresenter


def render(auth_service, current_user) -> None:
    """
    Vista de gestión de usuarios y seguridad.
    
    Args:
        auth_service: Servicio de autenticación
        current_user: Usuario actual de la sesión
    """
    st.header("🔐 Gestión de Usuarios y Seguridad")
    
    # Mostrar información del usuario actual
    if current_user:
        st.info(f"👤 Usuario actual: **{current_user.username}** ({current_user.role})")
    
    # Sub-tabs para gestión de usuarios
    sub_users, sub_new_user = st.tabs(["📋 Lista de Usuarios", "➕ Nuevo Usuario"])
    
    with sub_users:
        _render_user_list(auth_service, current_user)
    
    with sub_new_user:
        _render_new_user_form(auth_service)


def _render_user_list(auth_service, current_user) -> None:
    """Renderiza la lista de usuarios con acciones rápidas."""
    st.subheader("Usuarios del Sistema")
    
    try:
        users = auth_service.get_all_users()
    except Exception as e:
        st.error(f"Error al cargar usuarios: {e}")
        return
    
    if not users:
        st.info("No hay usuarios registrados en el sistema.")
        return
    
    # Tabla de usuarios
    user_data = []
    for u in users:
        user_data.append({
            "ID": u.id,
            "Usuario": u.username,
            "Nombre": u.full_name,
            "Email": u.email,
            "Rol": u.role,
            "Estado": StatusPresenter.get_user_status_display(u.is_active)
        })
    
    st.dataframe(user_data, width='stretch', hide_index=True)
    
    # Acciones rápidas
    st.divider()
    st.markdown("### Acciones Rápidas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        _render_change_password_form(auth_service, users)
    
    with col2:
        _render_toggle_user_status(auth_service, users, current_user)


def _render_change_password_form(auth_service, users) -> None:
    """Formulario para cambiar contraseña de usuario."""
    with st.expander("🔑 Cambiar Contraseña"):
        user_opts = {u.username: u.id for u in users}
        sel_user = st.selectbox(
            "Usuario", 
            list(user_opts.keys()), 
            key="pwd_user"
        )
        new_pwd = st.text_input(
            "Nueva Contraseña", 
            type="password", 
            key="new_pwd"
        )
        confirm_pwd = st.text_input(
            "Confirmar Contraseña", 
            type="password", 
            key="confirm_pwd"
        )
        
        if st.button("💾 Cambiar", key="btn_pwd"):
            if not new_pwd:
                st.error("❌ La contraseña no puede estar vacía")
            elif new_pwd != confirm_pwd:
                st.error("❌ Las contraseñas no coinciden")
            else:
                try:
                    if auth_service.change_password(user_opts[sel_user], new_pwd):
                        st.success("✅ Contraseña cambiada exitosamente")
                    else:
                        st.error("❌ Error al cambiar contraseña")
                except Exception as e:
                    st.error(f"❌ Error: {e}")


def _render_toggle_user_status(auth_service, users, current_user) -> None:
    """Formulario para activar/desactivar usuarios."""
    with st.expander("🔄 Activar/Desactivar Usuario"):
        inactive_users = [u for u in users if not u.is_active]
        active_users = [u for u in users if u.is_active and u.id != current_user.id]
        
        # Activar usuarios
        if inactive_users:
            st.markdown("**Activar Usuario:**")
            inactive_opts = {u.username: u.id for u in inactive_users}
            sel_inactive = st.selectbox(
                "Usuario Inactivo",
                list(inactive_opts.keys()),
                key="activate_user"
            )
            if st.button("✅ Activar", key="btn_activate"):
                try:
                    if auth_service.set_user_active(inactive_opts[sel_inactive], True):
                        st.success(f"✅ Usuario {sel_inactive} activado")
                        st.rerun()
                    else:
                        st.error("❌ Error al activar usuario")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.info("No hay usuarios inactivos")
        
        st.divider()
        
        # Desactivar usuarios
        if active_users:
            st.markdown("**Desactivar Usuario:**")
            active_opts = {u.username: u.id for u in active_users}
            sel_active = st.selectbox(
                "Usuario Activo",
                list(active_opts.keys()),
                key="deactivate_user"
            )
            if st.button("❌ Desactivar", key="btn_deactivate", type="secondary"):
                try:
                    if auth_service.set_user_active(active_opts[sel_active], False):
                        st.success(f"✅ Usuario {sel_active} desactivado")
                        st.rerun()
                    else:
                        st.error("❌ Error al desactivar usuario")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.info("No hay otros usuarios activos para desactivar")


def _render_new_user_form(auth_service) -> None:
    """Formulario para crear nuevo usuario."""
    st.subheader("Crear Nuevo Usuario")
    
    with st.form("new_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Nombre de Usuario *",
                placeholder="ej. jperez",
                help="Identificador único para login"
            )
            full_name = st.text_input(
                "Nombre Completo *",
                placeholder="ej. Juan Pérez"
            )
            email = st.text_input(
                "Email",
                placeholder="ej. jperez@empresa.com"
            )
        
        with col2:
            password = st.text_input(
                "Contraseña *",
                type="password"
            )
            confirm_password = st.text_input(
                "Confirmar Contraseña *",
                type="password"
            )
            role = st.selectbox(
                "Rol *",
                ["operator", "supervisor", "admin"],
                help="operator: Operaciones diarias | supervisor: Gestión | admin: Administración total"
            )
        
        submitted = st.form_submit_button("💾 Crear Usuario", type="primary")
        
        if submitted:
            # Validaciones
            if not username or not full_name or not password:
                st.error("⚠️ Complete los campos obligatorios (*)")
            elif password != confirm_password:
                st.error("❌ Las contraseñas no coinciden")
            elif len(password) < 4:
                st.error("❌ La contraseña debe tener al menos 4 caracteres")
            else:
                try:
                    new_user = auth_service.create_user(
                        username=username.strip(),
                        password=password,
                        full_name=full_name.strip(),
                        email=email.strip() if email else None,
                        role=role
                    )
                    if new_user:
                        st.success(f"✅ Usuario '{username}' creado exitosamente")
                    else:
                        st.error("❌ Error al crear usuario (puede que ya exista)")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

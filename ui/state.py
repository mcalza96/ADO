"""
Application State Keys - Constantes para manejar el session state de Streamlit

Evita el uso de magic strings para claves del session state, previniendo
bugs silenciosos por typos.

Usage:
    from ui.state import AppState
    
    # En lugar de:
    st.session_state['selected_site_id'] = 123
    
    # Usar:
    st.session_state[AppState.SELECTED_SITE_ID] = 123
"""


class AppState:
    """
    Constantes para las claves del session state de Streamlit.
    
    Agrupa las claves por módulo/funcionalidad para mejor organización.
    """
    
    # ==========================================
    # AUTENTICACIÓN
    # ==========================================
    USER = 'user'
    USER_ROLE = 'user_role'
    USER_ID = 'user_id'
    
    # ==========================================
    # UBICACIONES (Sites & Plots)
    # ==========================================
    SELECTED_SITE_ID = 'selected_site_id'
    SELECTED_PLOT_ID = 'selected_plot_id'
    PLOT_EDIT_ID = 'plot_edit_id'
    SITE_EDIT_MODE = 'site_edit_mode'
    
    # ==========================================
    # LOGÍSTICA
    # ==========================================
    SELECTED_LOAD_ID = 'selected_load_id'
    CURRENT_DISPATCH_ID = 'current_dispatch_id'
    SELECTED_VEHICLE_ID = 'selected_vehicle_id'
    SELECTED_DRIVER_ID = 'selected_driver_id'
    
    # ==========================================
    # TRATAMIENTO
    # ==========================================
    SELECTED_PLANT_ID = 'selected_plant_id'
    SELECTED_BATCH_ID = 'selected_batch_id'
    CURRENT_RECEPTION_ID = 'current_reception_id'
    
    # ==========================================
    # DISPOSICIÓN
    # ==========================================
    DISPOSAL_SITE_ID = 'disposal_site_id'
    DISPOSAL_LOAD_ID = 'disposal_load_id'
    
    # ==========================================
    # FORMULARIOS
    # ==========================================
    FORM_MODE = 'form_mode'
    FORM_EDIT_ID = 'form_edit_id'
    FORM_DATA = 'form_data'
    
    # ==========================================
    # NAVEGACIÓN
    # ==========================================
    CURRENT_PAGE = 'current_page'
    PREVIOUS_PAGE = 'previous_page'
    NAV_HISTORY = 'nav_history'
    
    # ==========================================
    # FILTROS Y BÚSQUEDA
    # ==========================================
    DATE_RANGE_START = 'date_range_start'
    DATE_RANGE_END = 'date_range_end'
    SEARCH_QUERY = 'search_query'
    FILTER_STATUS = 'filter_status'
    
    # ==========================================
    # TAREAS (INBOX)
    # ==========================================
    SELECTED_TASK_ID = 'selected_task_id'
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    @classmethod
    def init_if_missing(cls, key: str, default_value=None) -> None:
        """
        Inicializa una clave en session_state si no existe.
        
        Args:
            key: La constante de AppState a inicializar
            default_value: Valor por defecto si la clave no existe
        """
        import streamlit as st
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    @classmethod
    def get(cls, key: str, default=None):
        """
        Obtiene un valor del session_state de forma segura.
        
        Args:
            key: La constante de AppState
            default: Valor por defecto si no existe
            
        Returns:
            El valor almacenado o el default
        """
        import streamlit as st
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value) -> None:
        """
        Establece un valor en session_state.
        
        Args:
            key: La constante de AppState
            value: El valor a almacenar
        """
        import streamlit as st
        st.session_state[key] = value
    
    @classmethod
    def clear(cls, key: str) -> None:
        """
        Elimina una clave del session_state si existe.
        
        Args:
            key: La constante de AppState a eliminar
        """
        import streamlit as st
        if key in st.session_state:
            del st.session_state[key]

"""
Status Presenter - Maneja la presentación de estados en toda la UI

Centraliza:
- Colores de estados
- Etiquetas de estados
- Íconos/emojis de estados

Evita magic strings dispersos en múltiples archivos.
"""

from typing import Dict, Tuple, Optional
from enum import Enum


class RequestStatus(str, Enum):
    """Estados de solicitudes de retiro."""
    PENDING = "PENDING"
    PARTIALLY_SCHEDULED = "PARTIALLY_SCHEDULED"
    FULLY_SCHEDULED = "FULLY_SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LoadStatusDisplay(str, Enum):
    """Estados de cargas para display."""
    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"
    EN_ROUTE_DESTINATION = "EN_ROUTE_DESTINATION"
    AT_DESTINATION = "AT_DESTINATION"
    UNLOADING = "UNLOADING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ContainerStatus(str, Enum):
    """Estados de contenedores."""
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class StatusPresenter:
    """
    Presenter centralizado para estados.
    
    Uso:
        icon = StatusPresenter.get_request_icon("PENDING")  # 🟡
        label = StatusPresenter.get_request_label("PENDING")  # "Pendiente"
        color = StatusPresenter.get_request_color("PENDING")  # "yellow"
    """
    
    # ==========================================
    # REQUEST STATUS (Solicitudes de Retiro)
    # ==========================================
    
    _REQUEST_CONFIG: Dict[str, Tuple[str, str, str]] = {
        # status: (icon, label, color)
        "PENDING": ("🟡", "Pendiente", "yellow"),
        "PARTIALLY_SCHEDULED": ("🟠", "Parcialmente Programada", "orange"),
        "FULLY_SCHEDULED": ("🔵", "Programada", "blue"),
        "IN_PROGRESS": ("🟢", "En Progreso", "green"),
        "COMPLETED": ("✅", "Completada", "gray"),
        "CANCELLED": ("❌", "Cancelada", "red"),
    }
    
    @classmethod
    def get_request_icon(cls, status: str) -> str:
        """Obtiene el ícono para un estado de solicitud."""
        return cls._REQUEST_CONFIG.get(status, ("⚪", "", ""))[0]
    
    @classmethod
    def get_request_label(cls, status: str) -> str:
        """Obtiene la etiqueta para un estado de solicitud."""
        return cls._REQUEST_CONFIG.get(status, ("", status, ""))[1]
    
    @classmethod
    def get_request_color(cls, status: str) -> str:
        """Obtiene el color para un estado de solicitud."""
        return cls._REQUEST_CONFIG.get(status, ("", "", "gray"))[2]
    
    @classmethod
    def get_request_display(cls, status: str) -> str:
        """Obtiene display completo: ícono + etiqueta."""
        icon = cls.get_request_icon(status)
        label = cls.get_request_label(status)
        return f"{icon} {label}"
    
    @classmethod
    def get_expanded_states(cls) -> list:
        """Estados que deben mostrarse expandidos por defecto."""
        return ['PENDING', 'PARTIALLY_SCHEDULED', 'IN_PROGRESS']
    
    # ==========================================
    # CONTAINER STATUS
    # ==========================================
    
    _CONTAINER_CONFIG: Dict[str, Tuple[str, str]] = {
        # status: (emoji, description)
        "AVAILABLE": ("✅", "Disponible para uso"),
        "MAINTENANCE": ("🔧", "En mantenimiento"),
        "DECOMMISSIONED": ("🚫", "Dado de baja"),
    }
    
    @classmethod
    def get_container_icon(cls, status: str) -> str:
        """Obtiene el emoji para un estado de contenedor."""
        return cls._CONTAINER_CONFIG.get(status, ("❓", ""))[0]
    
    @classmethod
    def get_container_description(cls, status: str) -> str:
        """Obtiene la descripción para un estado de contenedor."""
        return cls._CONTAINER_CONFIG.get(status, ("", "Desconocido"))[1]
    
    @classmethod
    def get_container_display(cls, status: str) -> str:
        """Display: emoji + status."""
        icon = cls.get_container_icon(status)
        return f"{icon} {status}"
    
    # ==========================================
    # LOAD STATUS (Cargas)
    # ==========================================
    
    _LOAD_CONFIG: Dict[str, Tuple[str, str, str]] = {
        # status: (icon, label, badge_color)
        "REQUESTED": ("📝", "Solicitada", "blue"),
        "ASSIGNED": ("📋", "Asignada", "cyan"),
        "EN_ROUTE": ("🚛", "En Ruta", "orange"),
        "EN_ROUTE_DESTINATION": ("🚛", "En Ruta a Destino", "orange"),
        "AT_DESTINATION": ("📍", "En Destino", "yellow"),
        "UNLOADING": ("⏬", "Descargando", "purple"),
        "COMPLETED": ("✅", "Completada", "green"),
        "CANCELLED": ("❌", "Cancelada", "red"),
    }
    
    @classmethod
    def get_load_icon(cls, status: str) -> str:
        """Obtiene el ícono para un estado de carga."""
        return cls._LOAD_CONFIG.get(status, ("❓", "", ""))[0]
    
    @classmethod
    def get_load_label(cls, status: str) -> str:
        """Obtiene la etiqueta para un estado de carga."""
        return cls._LOAD_CONFIG.get(status, ("", status, ""))[1]
    
    @classmethod
    def get_load_badge_color(cls, status: str) -> str:
        """Obtiene el color de badge para un estado de carga."""
        return cls._LOAD_CONFIG.get(status, ("", "", "gray"))[2]
    
    @classmethod
    def get_load_display(cls, status: str) -> str:
        """Display completo: ícono + etiqueta."""
        icon = cls.get_load_icon(status)
        label = cls.get_load_label(status)
        return f"{icon} {label}"
    
    # ==========================================
    # USER STATUS
    # ==========================================
    
    @staticmethod
    def get_user_status_display(is_active: bool) -> str:
        """Display de estado de usuario."""
        return "✅ Activo" if is_active else "❌ Inactivo"
    
    # ==========================================
    # GENERIC HELPERS
    # ==========================================
    
    @staticmethod
    def format_boolean(value: bool, true_text: str = "✓", false_text: str = "✗") -> str:
        """Formatea un booleano para display."""
        return true_text if value else false_text
    
    @staticmethod
    def format_optional(value: Optional[str], default: str = "—") -> str:
        """Formatea un valor opcional, mostrando placeholder si es None."""
        return value if value else default
    
    # ==========================================
    # TASK PRIORITY (Tareas de Inbox)
    # ==========================================
    
    _PRIORITY_CONFIG: Dict[str, Tuple[str, str, str]] = {
        # priority: (icon, color, estimated_time)
        "High": ("🔴", "red", "5 min"),
        "Medium": ("🟡", "orange", "3 min"),
        "Low": ("🔵", "blue", "2 min"),
    }
    _DEFAULT_PRIORITY = ("⚪", "gray", "N/A")
    
    @classmethod
    def get_priority_icon(cls, priority: str) -> str:
        """Obtiene el ícono para una prioridad de tarea."""
        return cls._PRIORITY_CONFIG.get(priority, cls._DEFAULT_PRIORITY)[0]
    
    @classmethod
    def get_priority_color(cls, priority: str) -> str:
        """Obtiene el color para una prioridad de tarea."""
        return cls._PRIORITY_CONFIG.get(priority, cls._DEFAULT_PRIORITY)[1]
    
    @classmethod
    def get_priority_estimate(cls, priority: str) -> str:
        """Obtiene el tiempo estimado para una prioridad de tarea."""
        return cls._PRIORITY_CONFIG.get(priority, cls._DEFAULT_PRIORITY)[2]
    
    @classmethod
    def get_priority_config(cls, priority: str) -> Dict[str, str]:
        """
        Obtiene la configuración completa para una prioridad.
        
        Returns:
            Dict con keys: icon, color, estimate
        """
        config = cls._PRIORITY_CONFIG.get(priority, cls._DEFAULT_PRIORITY)
        return {
            "icon": config[0],
            "color": config[1],
            "estimate": config[2]
        }

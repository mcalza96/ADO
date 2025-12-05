"""
UI Constants - Enums y constantes para evitar magic strings en la interfaz

Este módulo centraliza:
- Tipos de destino
- Estados de formularios
- Regiones geográficas
- Configuración de thresholds
"""
from enum import Enum
from typing import List, Tuple
from domain.shared.enums import DisplayableEnum


# ==========================================
# DESTINATION TYPES
# ==========================================

class DestinationType(DisplayableEnum):
    """Tipos de destino para asignación de cargas"""
    FIELD_SITE = "FIELD_SITE"      # Campo/Sitio (aplicación agrícola)
    TREATMENT_PLANT = "TREATMENT_PLANT"  # Planta de tratamiento
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        return {
            DestinationType.FIELD_SITE: "Campo (Sitio)",
            DestinationType.TREATMENT_PLANT: "Planta (Tratamiento)"
        }.get(self, self.value)
    
    # Alias para compatibilidad con código existente
    @property
    def display_label(self) -> str:
        """Alias de display_name para compatibilidad."""
        return self.display_name
    
    @classmethod
    def from_label(cls, label: str) -> 'DestinationType':
        """Convierte etiqueta de UI a enum"""
        return cls.from_display_name(label) or cls.FIELD_SITE
    
    @classmethod
    def get_labels(cls) -> list[str]:
        """Retorna lista de etiquetas para selectbox"""
        return cls.display_names_list()


# ==========================================
# FORM STATUS
# ==========================================

class FormStatus(str, Enum):
    """Estados de formularios en la UI"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


# ==========================================
# GEOGRAPHIC REGIONS (Chile)
# ==========================================

class Region(str, Enum):
    """Regiones de Chile para selección en formularios"""
    METROPOLITANA = "Metropolitana"
    VALPARAISO = "Valparaíso"
    OHIGGINS = "O'Higgins"
    MAULE = "Maule"
    BIOBIO = "Biobío"
    ARAUCANIA = "Araucanía"
    LOS_LAGOS = "Los Lagos"
    
    @classmethod
    def get_list(cls) -> List[str]:
        """Retorna lista de regiones para selectbox"""
        return [r.value for r in cls]
    
    @classmethod
    def get_index(cls, region: str) -> int:
        """Obtiene el índice de una región (para preselección en selectbox)"""
        values = cls.get_list()
        try:
            return values.index(region) if region in values else 0
        except ValueError:
            return 0


# ==========================================
# DEFAULT COORDINATES (Chile)
# ==========================================

class DefaultCoordinates:
    """Coordenadas por defecto para mapas y formularios"""
    # Santiago, Chile
    LATITUDE = -33.4489
    LONGITUDE = -70.6693
    
    @classmethod
    def get_tuple(cls) -> Tuple[float, float]:
        """Retorna (lat, lon) como tupla"""
        return (cls.LATITUDE, cls.LONGITUDE)


# ==========================================
# OPERATIONAL THRESHOLDS
# ==========================================

class OperationalThresholds:
    """Umbrales operacionales para alertas y monitoreo"""
    
    # Logística
    DELAY_HOURS = 4.0  # Camiones con más de X horas en ruta = atrasados
    WAITING_ALERT_HOURS = 2.0  # Camiones esperando más de X horas = alerta
    
    # Capacidades
    MAX_CONTAINERS_PER_LOAD = 2
    MAX_LOADS_PER_REQUEST = 50
    
    # Pesos (kg)
    MIN_NET_WEIGHT = 0.0
    MAX_NET_WEIGHT = 50000.0
    DEFAULT_NET_WEIGHT = 15000.0
    
    # Contenedores (m³)
    MIN_CONTAINER_CAPACITY = 5.0
    MAX_CONTAINER_CAPACITY = 40.0
    DEFAULT_CONTAINER_CAPACITY = 20.0


# ==========================================
# UI CONFIGURATION
# ==========================================

class UIConfig:
    """Configuración general de la UI"""
    
    # Paginación
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Formatos de fecha
    DATE_FORMAT = "%d/%m/%Y"
    TIME_FORMAT = "%H:%M"
    DATETIME_FORMAT = "%d/%m/%Y %H:%M"
    
    # Decimal places
    AREA_DECIMALS = 2
    WEIGHT_DECIMALS = 0
    COORDINATE_DECIMALS = 6
    HOURS_DECIMALS = 1

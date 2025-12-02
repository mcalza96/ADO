"""
UI Constants - Enums para evitar magic strings en la interfaz
"""
from enum import Enum

class DestinationType(str, Enum):
    """Tipos de destino para asignación de cargas"""
    FIELD_SITE = "FIELD_SITE"      # Campo/Sitio (aplicación agrícola)
    TREATMENT_PLANT = "TREATMENT_PLANT"  # Planta de tratamiento
    
    @property
    def display_label(self) -> str:
        """Etiqueta amigable para mostrar en UI"""
        labels = {
            self.FIELD_SITE: "Campo (Sitio)",
            self.TREATMENT_PLANT: "Planta (Tratamiento)"
        }
        return labels[self]
    
    @classmethod
    def from_label(cls, label: str) -> 'DestinationType':
        """Convierte etiqueta de UI a enum"""
        mapping = {
            "Campo (Sitio)": cls.FIELD_SITE,
            "Planta (Tratamiento)": cls.TREATMENT_PLANT
        }
        return mapping.get(label, cls.FIELD_SITE)
    
    @classmethod
    def get_labels(cls) -> list[str]:
        """Retorna lista de etiquetas para selectbox"""
        return [dt.display_label for dt in cls]


class FormStatus(str, Enum):
    """Estados de formularios en la UI"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

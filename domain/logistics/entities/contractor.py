from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ContractorType(str, Enum):
    """
    Tipos de contratistas/proveedores del sistema.
    Extensible para futuros tipos (SERVICES, MECHANICS, etc.)
    """
    TRANSPORT = "TRANSPORT"      # Transportistas
    DISPOSAL = "DISPOSAL"        # Contratistas de disposición
    # Futuros tipos:
    # SERVICES = "SERVICES"      # Prestadores de servicios varios
    # MECHANICS = "MECHANICS"    # Mecánicos
    
    @classmethod
    def choices(cls) -> list:
        """Retorna lista de opciones para selectbox."""
        return [member.value for member in cls]
    
    @classmethod
    def labels(cls) -> dict:
        """Retorna mapeo de valores a etiquetas amigables."""
        return {
            cls.TRANSPORT.value: "Transportista",
            cls.DISPOSAL.value: "Disposición",
        }
    
    def label(self) -> str:
        """Retorna etiqueta amigable del tipo."""
        return self.labels().get(self.value, self.value)


@dataclass
class Contractor:
    id: Optional[int]
    name: str
    rut: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    contractor_type: str = ContractorType.TRANSPORT.value  # Tipo de contratista
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



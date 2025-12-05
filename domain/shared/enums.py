"""
DisplayableEnum - Base class para enums con soporte de UI.

Proporciona una interfaz estándar para:
- Almacenamiento en BD (value)
- Display en UI (display_name)
- Selectboxes/Multiselects (choices)
- Serialización CSV para campos multi-valor

CONVENCIÓN IMPORTANTE:
- choices() retorna List[(display_name, value)] para compatibilidad con GenericMasterView
- El VALUE es lo que se guarda en la base de datos
- El DISPLAY_NAME es lo que se muestra al usuario
"""

from enum import Enum
from typing import List, Optional, Dict, Any


class DisplayableEnum(str, Enum):
    """
    Base class para enums que necesitan display names en UI.
    
    Uso:
        class MyEnum(DisplayableEnum):
            OPTION_A = "OPTION_A"
            OPTION_B = "OPTION_B"
            
            @property
            def display_name(self) -> str:
                return {
                    MyEnum.OPTION_A: "Opción A (descripción)",
                    MyEnum.OPTION_B: "Opción B (descripción)"
                }.get(self, self.value)
    """
    
    @property
    def display_name(self) -> str:
        """
        Nombre legible para mostrar en UI.
        Debe ser sobrescrito por cada enum específico.
        """
        return self.value
    
    @classmethod
    def choices(cls) -> List[tuple]:
        """
        Lista de opciones para selectbox/multiselect.
        
        Returns:
            List[(display_name, value)] - El orden es importante:
            - display_name: lo que ve el usuario
            - value: lo que se guarda en BD
        """
        return [(e.display_name, e.value) for e in cls]
    
    @classmethod
    def values_list(cls) -> List[str]:
        """Lista de valores válidos para validación."""
        return [e.value for e in cls]
    
    @classmethod
    def display_names_list(cls) -> List[str]:
        """Lista de nombres para mostrar."""
        return [e.display_name for e in cls]
    
    @classmethod
    def from_display_name(cls, display_name: str) -> Optional['DisplayableEnum']:
        """Obtiene enum desde su display_name."""
        for e in cls:
            if e.display_name == display_name:
                return e
        return None
    
    @classmethod
    def from_csv(cls, csv_string: str) -> List['DisplayableEnum']:
        """
        Convierte CSV de valores a lista de enums.
        Ejemplo: 'VALUE_A,VALUE_B' -> [Enum.VALUE_A, Enum.VALUE_B]
        """
        if not csv_string:
            return list(cls)  # Sin restricción = todos permitidos
        
        result = []
        for value in csv_string.split(','):
            value = value.strip()
            if value:
                try:
                    result.append(cls(value))
                except ValueError:
                    # Intentar desde display_name (para datos legacy)
                    enum_val = cls.from_display_name(value)
                    if enum_val:
                        result.append(enum_val)
        return result
    
    @classmethod
    def to_csv(cls, enums: List['DisplayableEnum']) -> str:
        """
        Convierte lista de enums a CSV de valores.
        Ejemplo: [Enum.VALUE_A, Enum.VALUE_B] -> 'VALUE_A,VALUE_B'
        """
        return ','.join(e.value for e in enums)
    
    @classmethod
    def is_valid_value(cls, value: str) -> bool:
        """Verifica si un string es un valor válido del enum."""
        return value in cls.values_list()
    
    @classmethod
    def validate_or_raise(cls, value: str, field_name: str = "value") -> 'DisplayableEnum':
        """
        Valida y retorna el enum, o lanza error descriptivo.
        
        Args:
            value: El valor a validar
            field_name: Nombre del campo para el mensaje de error
            
        Raises:
            ValueError: Si el valor no es válido
        """
        if not value:
            raise ValueError(f"{field_name} no puede estar vacío")
        
        # Primero intentar como valor directo
        if cls.is_valid_value(value):
            return cls(value)
        
        # Luego intentar como display_name (error común)
        enum_val = cls.from_display_name(value)
        if enum_val:
            raise ValueError(
                f"'{value}' parece ser un display_name, no un valor válido. "
                f"Use '{enum_val.value}' en su lugar. "
                f"Valores válidos: {cls.values_list()}"
            )
        
        raise ValueError(
            f"'{value}' no es un valor válido para {field_name}. "
            f"Valores válidos: {cls.values_list()}"
        )

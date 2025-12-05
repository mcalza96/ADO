"""
UI Input Helpers - Componentes reutilizables para formularios

Este módulo proporciona funciones helper para evitar la repetición
del patrón "selectbox from service" en las vistas.
"""

import streamlit as st
from typing import Any, Optional, Callable, List


def select_entity(
    label: str,
    service: Any,
    key: Optional[str] = None,
    key_attr: str = 'id',
    display_attr: str = 'name',
    filter_func: Optional[Callable] = None,
    empty_message: Optional[str] = None,
    allow_none: bool = False,
    none_label: str = "-- Seleccione --",
    help_text: Optional[str] = None
) -> Optional[Any]:
    """
    Helper para crear un selectbox a partir de un servicio CRUD.
    
    Elimina la repetición del patrón:
        items = service.get_all()
        opts = {i.name: i.id for i in items}
        selected_name = st.selectbox("Label", list(opts.keys()))
        selected_id = opts[selected_name]
    
    Args:
        label: Etiqueta del selectbox
        service: Servicio con método get_all() que retorna entidades
        key: Key única de Streamlit para el widget (opcional)
        key_attr: Atributo de la entidad a retornar (default: 'id')
        display_attr: Atributo de la entidad a mostrar (default: 'name')
        filter_func: Función opcional para filtrar items (ej. lambda x: x.is_active)
        empty_message: Mensaje a mostrar si no hay items
        allow_none: Si True, agrega opción "Ninguno" al inicio
        none_label: Etiqueta para la opción None
        help_text: Texto de ayuda para el selectbox
    
    Returns:
        El valor del atributo key_attr de la entidad seleccionada, o None
    
    Example:
        # Antes (repetitivo):
        plants = plant_service.get_all()
        p_opts = {p.name: p.id for p in plants}
        sel_plant_name = st.selectbox("Seleccione Planta", list(p_opts.keys()))
        plant_id = p_opts[sel_plant_name]
        
        # Después (limpio):
        plant_id = select_entity("Seleccione Planta", plant_service)
    """
    # Obtener items del servicio
    try:
        items = service.get_all()
    except Exception as e:
        st.error(f"Error al cargar datos para '{label}': {e}")
        return None
    
    # Aplicar filtro si existe
    if filter_func:
        items = [i for i in items if filter_func(i)]
    
    # Verificar si hay items
    if not items:
        msg = empty_message or f"No hay registros disponibles para {label}"
        st.warning(msg)
        return None
    
    # Construir mapeo display -> key_attr
    options_map = {}
    for item in items:
        display_value = getattr(item, display_attr, str(item))
        key_value = getattr(item, key_attr, item)
        options_map[display_value] = key_value
    
    # Preparar opciones
    options = list(options_map.keys())
    
    if allow_none:
        options = [none_label] + options
    
    # Renderizar selectbox
    selected_label = st.selectbox(
        label,
        options=options,
        key=key,
        help=help_text
    )
    
    # Retornar valor
    if allow_none and selected_label == none_label:
        return None
    
    return options_map.get(selected_label)


def select_entity_full(
    label: str,
    service: Any,
    key: Optional[str] = None,
    display_attr: str = 'name',
    filter_func: Optional[Callable] = None,
    empty_message: Optional[str] = None,
    help_text: Optional[str] = None
) -> Optional[Any]:
    """
    Similar a select_entity pero retorna la entidad completa en lugar de solo el ID.
    
    Útil cuando necesitas acceder a múltiples atributos de la entidad seleccionada.
    
    Args:
        label: Etiqueta del selectbox
        service: Servicio con método get_all()
        key: Key única de Streamlit
        display_attr: Atributo a mostrar
        filter_func: Función de filtrado
        empty_message: Mensaje si no hay items
        help_text: Texto de ayuda
    
    Returns:
        La entidad completa seleccionada, o None
    
    Example:
        vehicle = select_entity_full("Vehículo", vehicle_service)
        if vehicle:
            st.write(f"Patente: {vehicle.plate}, Capacidad: {vehicle.capacity}")
    """
    try:
        items = service.get_all()
    except Exception as e:
        st.error(f"Error al cargar datos para '{label}': {e}")
        return None
    
    if filter_func:
        items = [i for i in items if filter_func(i)]
    
    if not items:
        msg = empty_message or f"No hay registros disponibles para {label}"
        st.warning(msg)
        return None
    
    # Mapeo display -> entidad completa
    options_map = {getattr(item, display_attr, str(item)): item for item in items}
    
    selected_label = st.selectbox(
        label,
        options=list(options_map.keys()),
        key=key,
        help=help_text
    )
    
    return options_map.get(selected_label)


def multiselect_entities(
    label: str,
    service: Any,
    key: Optional[str] = None,
    key_attr: str = 'id',
    display_attr: str = 'name',
    filter_func: Optional[Callable] = None,
    default: Optional[List] = None,
    help_text: Optional[str] = None
) -> List[Any]:
    """
    Helper para crear un multiselect a partir de un servicio CRUD.
    
    Args:
        label: Etiqueta del multiselect
        service: Servicio con método get_all()
        key: Key única de Streamlit
        key_attr: Atributo a retornar
        display_attr: Atributo a mostrar
        filter_func: Función de filtrado
        default: Lista de valores por defecto (display values)
        help_text: Texto de ayuda
    
    Returns:
        Lista de valores key_attr de las entidades seleccionadas
    """
    try:
        items = service.get_all()
    except Exception as e:
        st.error(f"Error al cargar datos para '{label}': {e}")
        return []
    
    if filter_func:
        items = [i for i in items if filter_func(i)]
    
    if not items:
        st.warning(f"No hay registros disponibles para {label}")
        return []
    
    options_map = {getattr(item, display_attr, str(item)): getattr(item, key_attr, item) for item in items}
    
    selected_labels = st.multiselect(
        label,
        options=list(options_map.keys()),
        default=default,
        key=key,
        help=help_text
    )
    
    return [options_map[lbl] for lbl in selected_labels]

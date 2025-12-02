"""
Transition Validators - Verificadores de Checkpoints

Estos validadores actúan como "llaves" que deben cumplirse antes de permitir
ciertas transiciones de estado. Leen datos del campo `attributes` (JSONB)
de la entidad Load.

Ejemplo de uso:
    load.attributes = {
        'entry_weight_ticket': 'TKT-12345',
        'lab_analysis_result': {'ph': 7.2, 'solids': 3.5},
        'exit_weight_ticket': 'TKT-12346'
    }
    
    ensure_entry_weight(load.attributes)  # OK
    ensure_lab_analysis(load.attributes)  # OK
    ensure_exit_weight(load.attributes)   # OK
"""
from typing import Dict, Any
from domain.shared.exceptions import DomainException


def ensure_entry_weight(attributes: Dict[str, Any]) -> None:
    """
    Valida que exista el ticket de pesaje de entrada.
    
    Requerido para: Transición a COMPLETED (caso tratamiento)
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    if not attributes.get('entry_weight_ticket'):
        raise DomainException(
            "Falta verificador: Pesaje de entrada (entry_weight_ticket)"
        )


def ensure_lab_analysis(attributes: Dict[str, Any]) -> None:
    """
    Valida que exista el resultado de análisis de laboratorio.
    
    Requerido para: Transición a COMPLETED (caso tratamiento)
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    lab_result = attributes.get('lab_analysis_result')
    if not lab_result:
        raise DomainException(
            "Falta verificador: Análisis de laboratorio (lab_analysis_result)"
        )
    
    # Validación adicional: verificar que tenga datos mínimos
    if isinstance(lab_result, dict):
        if 'ph' not in lab_result and 'solids' not in lab_result:
            raise DomainException(
                "Análisis de laboratorio incompleto: debe incluir pH o sólidos"
            )


def ensure_exit_weight(attributes: Dict[str, Any]) -> None:
    """
    Valida que exista el ticket de pesaje de salida.
    
    Requerido para: Transición a COMPLETED (caso tratamiento)
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    if not attributes.get('exit_weight_ticket'):
        raise DomainException(
            "Falta verificador: Pesaje de salida (exit_weight_ticket)"
        )


def ensure_gate_entry(attributes: Dict[str, Any]) -> None:
    """
    Valida el registro en portería (gate check).
    
    Requerido para: Transición de EN_ROUTE_DESTINATION a AT_DESTINATION
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    gate_check = attributes.get('gate_entry_check')
    if not gate_check:
        raise DomainException(
            "Falta verificador: Registro en portería (gate_entry_check)"
        )
    
    # Validación adicional: verificar timestamp
    if isinstance(gate_check, dict) and not gate_check.get('timestamp'):
        raise DomainException(
            "Registro de portería incompleto: falta timestamp"
        )


def ensure_pickup_confirmation(attributes: Dict[str, Any]) -> None:
    """
    Valida que se haya confirmado la recolección en origen.
    
    Requerido para: Transición de AT_PICKUP a EN_ROUTE_DESTINATION
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    if not attributes.get('pickup_confirmation'):
        raise DomainException(
            "Falta verificador: Confirmación de carga (pickup_confirmation)"
        )


def ensure_driver_acceptance(attributes: Dict[str, Any]) -> None:
    """
    Valida que el conductor haya aceptado explícitamente el viaje.
    
    Requerido para: Transición de ASSIGNED a ACCEPTED
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    acceptance = attributes.get('driver_acceptance')
    if not acceptance:
        raise DomainException(
            "Falta verificador: Aceptación del conductor (driver_acceptance)"
        )
    
    # Validación adicional: verificar timestamp y user_id
    if isinstance(acceptance, dict):
        if not acceptance.get('timestamp') or not acceptance.get('driver_id'):
            raise DomainException(
                "Aceptación del conductor incompleta: falta timestamp o driver_id"
            )


def ensure_disposal_completion(attributes: Dict[str, Any]) -> None:
    """
    Valida que se haya completado el proceso de disposición/aplicación.
    
    Requerido para: Transición de IN_DISPOSAL a COMPLETED
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    disposal_data = attributes.get('disposal_completion')
    if not disposal_data:
        raise DomainException(
            "Falta verificador: Confirmación de disposición (disposal_completion)"
        )
    
    # Validación adicional: verificar datos agronómicos
    if isinstance(disposal_data, dict):
        required_fields = ['application_date', 'plot_id', 'operator_id']
        missing = [f for f in required_fields if not disposal_data.get(f)]
        if missing:
            raise DomainException(
                f"Disposición incompleta: faltan campos {', '.join(missing)}"
            )


def ensure_weight_ticket_final(attributes: Dict[str, Any]) -> None:
    """
    Valida que exista el ticket de pesaje final.
    
    Requerido para: Transición a COMPLETED (caso tratamiento)
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    if not attributes.get('weight_ticket_final'):
        raise DomainException(
            "Falta verificador: Ticket de pesaje final (weight_ticket_final)"
        )


def ensure_lab_analysis_ok(attributes: Dict[str, Any]) -> None:
    """
    Valida que el análisis de laboratorio esté aprobado.
    
    Requerido para: Transición a COMPLETED (caso tratamiento)
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador o no está aprobado
    """
    lab_ok = attributes.get('lab_analysis_ok')
    if not lab_ok:
        raise DomainException(
            "Falta verificador: Análisis de laboratorio aprobado (lab_analysis_ok debe ser True)"
        )


def ensure_geofence_confirmation(attributes: Dict[str, Any]) -> None:
    """
    Valida confirmación de geocerca o manual en punto de recolección.
    
    Requerido para: Transición a AT_PICKUP
    
    Args:
        attributes: Diccionario de atributos de la carga
        
    Raises:
        DomainException: Si falta el verificador
    """
    geofence = attributes.get('geofence_confirmation')
    manual = attributes.get('manual_pickup_confirmation')
    
    if not geofence and not manual:
        raise DomainException(
            "Falta verificador: Confirmación de geocerca o manual en pickup "
            "(geofence_confirmation o manual_pickup_confirmation)"
        )

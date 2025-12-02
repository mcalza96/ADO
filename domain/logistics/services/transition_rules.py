"""
Transition Rules - Registro de Reglas de Transición

Implementa el patrón Strategy/Registry para gestionar las reglas de transición
entre estados de manera extensible y mantenible.

Para agregar una nueva regla:
1. Crear un validador en transition_validators.py
2. Agregarlo al diccionario TRANSITION_RULES con el estado destino como clave

Ejemplo:
    # Para permitir transición a COMPLETED, se requieren estos 3 verificadores:
    TRANSITION_RULES[LoadStatus.COMPLETED] = [
        ensure_entry_weight,
        ensure_lab_analysis,
        ensure_exit_weight
    ]
"""
from typing import Dict, List, Callable, Optional
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.services.transition_validators import (
    ensure_entry_weight,
    ensure_lab_analysis,
    ensure_exit_weight,
    ensure_gate_entry,
    ensure_pickup_confirmation,
    ensure_driver_acceptance,
    ensure_disposal_completion,
    ensure_weight_ticket_final,
    ensure_lab_analysis_ok,
    ensure_geofence_confirmation,
)


# Type alias para funciones validadoras
ValidatorFunc = Callable[[Dict], None]


# ============================================================================
# REGISTRO DE REGLAS DE TRANSICIÓN
# ============================================================================
# Mapea estado destino -> lista de validadores requeridos
# 
# Nota: Solo se definen reglas para transiciones que requieren validación.
# Las transiciones sin entrada en este diccionario se permiten sin verificadores.
# ============================================================================

TRANSITION_RULES: Dict[LoadStatus, List[ValidatorFunc]] = {
    # Transición: ASSIGNED -> ACCEPTED
    # Requiere aceptación explícita del conductor
    LoadStatus.ACCEPTED: [
        ensure_driver_acceptance,
    ],
    
    # Transición: EN_ROUTE_PICKUP -> AT_PICKUP
    # Requiere confirmación de geocerca o manual
    LoadStatus.AT_PICKUP: [
        ensure_geofence_confirmation,
    ],
    
    # Transición: AT_PICKUP -> EN_ROUTE_DESTINATION
    # Requiere confirmación de que se completó la carga
    LoadStatus.EN_ROUTE_DESTINATION: [
        ensure_pickup_confirmation,
    ],
    
    # Transición: EN_ROUTE_DESTINATION -> AT_DESTINATION
    # Requiere registro en portería de la planta
    LoadStatus.AT_DESTINATION: [
        ensure_gate_entry,
    ],
    
    # Transición: AT_DESTINATION -> COMPLETED (Caso Tratamiento)
    # Requiere pesajes de entrada/salida y análisis de laboratorio aprobado
    LoadStatus.COMPLETED: [
        ensure_entry_weight,
        ensure_lab_analysis_ok,      # Actualizado: verifica aprobación explícita
        ensure_weight_ticket_final,   # Nuevo: ticket de pesaje final
    ],
    
    # Transición: IN_DISPOSAL -> COMPLETED (Caso Disposición)
    # Requiere confirmación de aplicación agronómica
    # Nota: Esta regla se aplica condicionalmente (ver get_validators_for_transition)
    # LoadStatus.COMPLETED ya está definido arriba para caso tratamiento
}


# Reglas específicas para flujo de disposición
DISPOSAL_COMPLETION_RULES: List[ValidatorFunc] = [
    ensure_disposal_completion,
]


def get_validators_for_transition(
    to_status: LoadStatus,
    from_status: Optional[LoadStatus] = None,
    is_disposal_flow: bool = False
) -> List[ValidatorFunc]:
    """
    Obtiene los validadores necesarios para una transición específica.
    
    Soporta lógica condicional basada en el tipo de flujo (tratamiento vs disposición).
    
    Args:
        to_status: Estado destino de la transición
        from_status: Estado origen (opcional, para lógica condicional)
        is_disposal_flow: True si la carga va a disposición/campo
        
    Returns:
        Lista de funciones validadoras a ejecutar
    """
    # Caso especial: COMPLETED con flujo de disposición
    if to_status == LoadStatus.COMPLETED and is_disposal_flow:
        # Si viene desde IN_DISPOSAL, requiere verificadores de disposición
        if from_status == LoadStatus.IN_DISPOSAL:
            return DISPOSAL_COMPLETION_RULES
    
    # Caso general: consultar registro de reglas
    return TRANSITION_RULES.get(to_status, [])


def get_all_transition_rules() -> Dict[LoadStatus, List[str]]:
    """
    Retorna un diccionario con todas las reglas definidas (para documentación/debug).
    
    Returns:
        Dict mapeando estado destino -> nombres de validadores
    """
    return {
        status: [v.__name__ for v in validators]
        for status, validators in TRANSITION_RULES.items()
    }


# ============================================================================
# MAPA DE TRANSICIONES VÁLIDAS (FSM - Máquina de Estados Finitos)
# ============================================================================
# Define qué transiciones están permitidas desde cada estado.
# Si una transición no está en este mapa, se considera inválida.
# ============================================================================

VALID_TRANSITIONS: Dict[LoadStatus, List[LoadStatus]] = {
    LoadStatus.REQUESTED: [
        LoadStatus.ASSIGNED,
    ],
    LoadStatus.ASSIGNED: [
        LoadStatus.ACCEPTED,
        LoadStatus.REQUESTED,  # Permite reasignación
    ],
    LoadStatus.ACCEPTED: [
        LoadStatus.EN_ROUTE_PICKUP,
        LoadStatus.ASSIGNED,  # Permite regresar si hay error
    ],
    LoadStatus.EN_ROUTE_PICKUP: [
        LoadStatus.AT_PICKUP,
    ],
    LoadStatus.AT_PICKUP: [
        LoadStatus.EN_ROUTE_DESTINATION,
    ],
    LoadStatus.EN_ROUTE_DESTINATION: [
        LoadStatus.AT_DESTINATION,
    ],
    LoadStatus.AT_DESTINATION: [
        LoadStatus.IN_DISPOSAL,  # Flujo disposición
        LoadStatus.COMPLETED,    # Flujo tratamiento
    ],
    LoadStatus.IN_DISPOSAL: [
        LoadStatus.COMPLETED,
    ],
}


def is_valid_transition(from_status: LoadStatus, to_status: LoadStatus) -> bool:
    """
    Valida si una transición es permitida según la FSM.
    
    Args:
        from_status: Estado origen
        to_status: Estado destino
        
    Returns:
        True si la transición es válida, False en caso contrario
    """
    allowed_transitions = VALID_TRANSITIONS.get(from_status, [])
    return to_status in allowed_transitions

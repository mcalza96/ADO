"""
LoadStatus Enum - Estados del Ciclo de Vida de la Carga

Diferenciación importante:
- Estados (States): Etapas macro donde la carga permanece un tiempo (medible para SLA)
- Verificadores (Checkpoints): Eventos puntuales que actúan como llaves para transiciones
  (no son estados, se almacenan en Load.attributes)
"""
from domain.shared.enums import DisplayableEnum


class LoadStatus(DisplayableEnum):
    """
    Estados del ciclo de vida de una carga.
    
    Flujo Típico:
    REQUESTED → ASSIGNED → ACCEPTED → EN_ROUTE_PICKUP → AT_PICKUP → 
    EN_ROUTE_DESTINATION → AT_DESTINATION → COMPLETED
    
    Flujo Alternativo (Disposición):
    ... → AT_DESTINATION → IN_DISPOSAL → COMPLETED
    """
    
    # Fase de Planificación
    REQUESTED = "REQUESTED"                     # Solicitud creada por cliente
    ASSIGNED = "ASSIGNED"                       # Asignado a conductor/camión
    
    # Fase de Aceptación
    ACCEPTED = "ACCEPTED"                       # Aceptado por conductor
    
    # Fase de Recolección
    EN_ROUTE_PICKUP = "EN_ROUTE_PICKUP"        # En ruta hacia origen
    AT_PICKUP = "AT_PICKUP"                     # En origen (proceso de carga)
    
    # Fase de Transporte
    EN_ROUTE_DESTINATION = "EN_ROUTE_DESTINATION"  # En ruta hacia destino
    
    # Fase de Recepción
    AT_DESTINATION = "AT_DESTINATION"           # En destino (planta/predio)
    
    # Fase de Disposición (Opcional - Solo para predios/campos)
    IN_DISPOSAL = "IN_DISPOSAL"                 # En proceso de disposición/aplicación
    
    # Fase Final
    COMPLETED = "COMPLETED"                     # Finalizado exitosamente
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        return {
            LoadStatus.REQUESTED: "🟡 Solicitado",
            LoadStatus.ASSIGNED: "🟠 Asignado",
            LoadStatus.ACCEPTED: "🟢 Aceptado",
            LoadStatus.EN_ROUTE_PICKUP: "🚚 En Ruta (Recogida)",
            LoadStatus.AT_PICKUP: "📦 En Origen",
            LoadStatus.EN_ROUTE_DESTINATION: "🚛 En Ruta (Destino)",
            LoadStatus.AT_DESTINATION: "🏭 En Destino",
            LoadStatus.IN_DISPOSAL: "🌾 En Disposición",
            LoadStatus.COMPLETED: "✅ Completado"
        }.get(self, self.value)


# Mapeo de compatibilidad con estados legacy
LEGACY_STATUS_MAPPING = {
    "Requested": LoadStatus.REQUESTED,
    "Scheduled": LoadStatus.ASSIGNED,
    "Accepted": LoadStatus.ACCEPTED,
    "InTransit": LoadStatus.EN_ROUTE_DESTINATION,
    "Arrived": LoadStatus.AT_DESTINATION,
    "Delivered": LoadStatus.COMPLETED,
}


def normalize_status(status: str) -> LoadStatus:
    """
    Convierte estados legacy al nuevo formato.
    
    Args:
        status: Estado en formato legacy o nuevo
        
    Returns:
        LoadStatus enum value
        
    Raises:
        ValueError: Si el estado no es válido
    """
    # Si ya es un LoadStatus válido
    try:
        return LoadStatus(status)
    except ValueError:
        pass
    
    # Intentar mapeo legacy
    if status in LEGACY_STATUS_MAPPING:
        return LEGACY_STATUS_MAPPING[status]
    
    raise ValueError(f"Invalid status: {status}")

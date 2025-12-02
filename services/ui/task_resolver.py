from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from domain.logistics.repositories.load_repository import LoadRepository
from domain.logistics.entities.load_status import LoadStatus
from domain.logistics.services.transition_rules import get_validators_for_transition, VALID_TRANSITIONS
from domain.logistics.services.transition_validators import (
    ensure_lab_analysis_ok, ensure_gate_entry, ensure_pickup_confirmation,
    ensure_entry_weight, ensure_exit_weight, ensure_weight_ticket_final,
    ensure_geofence_confirmation
)
from domain.agronomy.repositories.machine_log_repository import MachineLogRepository

@dataclass
class TaskViewModel:
    id: str # Unique ID for UI selection
    title: str
    description: str
    priority: str # High, Medium, Low
    form_type: str # Key for FormRegistry
    entity_id: int # load_id or machine_id
    entity_type: str # LOAD or MACHINE
    payload: Dict[str, Any] # Context data for the form

class TaskResolver:
    """
    Servicio de UI que determina qué tareas están pendientes para un usuario.
    Analiza el estado de las cargas y maquinaria para generar una "Bandeja de Entrada".
    """
    
    def __init__(self, load_repository, machine_log_repository):
        self.load_repo = load_repository
        self.log_repo = machine_log_repository
        
        # Mapeo de Validador -> Configuración de Tarea
        self.validator_map = {
            ensure_lab_analysis_ok.__name__: {
                "title": "Registrar Análisis de Laboratorio",
                "form_type": "lab_check",
                "priority": "High",
                "priority_order": 1,
                "allowed_roles": ["LAB_TECH", "ADMIN", "OPERATOR"]
            },
            ensure_gate_entry.__name__: {
                "title": "Registrar Ingreso en Portería",
                "form_type": "gate_check",
                "priority": "Medium",
                "priority_order": 3,
                "allowed_roles": ["GATE_KEEPER", "ADMIN", "OPERATOR"]
            },
            ensure_pickup_confirmation.__name__: {
                "title": "Confirmar Carga en Origen",
                "form_type": "pickup_check",
                "priority": "High",
                "priority_order": 2,
                "allowed_roles": ["DRIVER", "ADMIN", "OPERATOR"]
            },
            ensure_geofence_confirmation.__name__: {
                "title": "Confirmar Llegada a Origen",
                "form_type": "geofence_check",
                "priority": "Medium",
                "priority_order": 4,
                "allowed_roles": ["DRIVER", "ADMIN", "OPERATOR"]
            },
            ensure_entry_weight.__name__: {
                "title": "Registrar Pesaje de Entrada",
                "form_type": "weight_check",
                "priority": "High",
                "priority_order": 1,
                "allowed_roles": ["GATE_KEEPER", "ADMIN", "OPERATOR"]
            },
            ensure_exit_weight.__name__: {
                "title": "Registrar Pesaje de Salida",
                "form_type": "weight_check",
                "priority": "High",
                "priority_order": 1,
                "allowed_roles": ["GATE_KEEPER", "ADMIN", "OPERATOR"]
            },
            ensure_weight_ticket_final.__name__: {
                "title": "Subir Ticket de Pesaje Final",
                "form_type": "ticket_upload",
                "priority": "Medium",
                "priority_order": 5,
                "allowed_roles": ["ADMIN", "OPERATOR"]
            }
        }

    def get_pending_tasks(self, user_role: str, user_id: int) -> List[TaskViewModel]:
        """
        Obtiene lista de tareas pendientes filtradas por rol.
        
        Args:
            user_role: Rol del usuario (DRIVER, LAB_TECH, GATE_KEEPER, OPERATOR, ADMIN)
            user_id: ID del usuario
            
        Returns:
            Lista de TaskViewModel ordenadas por prioridad
        """
        tasks = []
        
        # 1. Tareas de Logística (Cargas)
        active_loads = self.load_repo.get_all() 
        active_loads = [l for l in active_loads if l.status != LoadStatus.COMPLETED.value]
        
        for load in active_loads:
            load_tasks = self._analyze_load(load, user_role)
            tasks.extend(load_tasks)
            
        # 2. Tareas de Maquinaria (Solo para operadores)
        if user_role in ['OPERATOR', 'ADMIN']:
            assigned_machines = self._get_assigned_machines(user_id)
            for machine_id in assigned_machines:
                machine_tasks = self._analyze_machine(machine_id, user_id)
                tasks.extend(machine_tasks)
        
        # 3. Ordenar por prioridad (High -> Medium -> Low) y luego por priority_order
        priority_value = {'High': 1, 'Medium': 2, 'Low': 3}
        tasks.sort(key=lambda t: (priority_value.get(t.priority, 999), getattr(t, 'priority_order', 999)))
             
        return tasks

    def _analyze_load(self, load, user_role: str) -> List[TaskViewModel]:
        """
        Analiza una carga y genera tareas pendientes filtradas por rol.
        
        Args:
            load: Objeto Load a analizar
            user_role: Rol del usuario actual
            
        Returns:
            Lista de TaskViewModel para esta carga
        """
        tasks = []
        current_status = LoadStatus(load.status) if isinstance(load.status, str) else load.status
        
        # Determinar siguiente estado lógico
        next_statuses = VALID_TRANSITIONS.get(current_status, [])
        if not next_statuses:
            return []
            
        # Simplificación: Tomamos el primer estado siguiente válido
        # En un caso real con bifurcaciones (Disposición vs Tratamiento), 
        # usaríamos load.destination_site_id para decidir.
        next_status = next_statuses[0]
        if len(next_statuses) > 1 and load.destination_site_id:
             # Si tiene sitio destino y hay opción de IN_DISPOSAL, preferir esa ruta
             if LoadStatus.IN_DISPOSAL in next_statuses:
                 next_status = LoadStatus.IN_DISPOSAL
        
        # Obtener validadores requeridos
        is_disposal = load.destination_site_id is not None
        validators = get_validators_for_transition(next_status, current_status, is_disposal)
        
        # Verificar cuáles faltan
        if not load.attributes:
            load.attributes = {}
        
        # Recolectar TODAS las tareas pendientes (hasta top 3)
        pending_validators = []
        for validator in validators:
            try:
                validator(load.attributes)
            except Exception:
                # Si falla, significa que falta este requisito
                config = self.validator_map.get(validator.__name__)
                if config and self._is_task_allowed_for_role(config, user_role):
                    pending_validators.append((validator, config))
        
        # Ordenar por priority_order y tomar top 3
        pending_validators.sort(key=lambda x: x[1].get('priority_order', 999))
        
        for validator, config in pending_validators[:3]:
            task = TaskViewModel(
                id=f"LOAD-{load.id}-{config['form_type']}",
                title=f"{config['title']} (Carga #{load.id})",
                description=f"Requerido para avanzar a {next_status.value}",
                priority=config['priority'],
                form_type=config['form_type'],
                entity_id=load.id,
                entity_type="LOAD",
                payload={'load': load, 'target_status': next_status.value}
            )
            # Agregar priority_order como atributo extra para sorting
            task.priority_order = config.get('priority_order', 999)
            tasks.append(task)
                    
        return tasks

    def _analyze_machine(self, machine_id: int, user_id: int) -> List[TaskViewModel]:
        """
        Verifica si una máquina requiere el parte diario de hoy.
        
        Args:
            machine_id: ID de la máquina a verificar
            user_id: ID del usuario operador
            
        Returns:
            Lista con tarea de MachineLog si está pendiente, lista vacía si no
        """
        # Verificar si ya existe log para hoy
        today_logs = self.log_repo.get_by_machine_id(machine_id)
        # Filtrar por fecha de hoy (simple check)
        has_log_today = any(l.date.date() == datetime.now().date() for l in today_logs)
        
        if not has_log_today:
            task = TaskViewModel(
                id=f"MACHINE-{machine_id}-DAILY",
                title=f"Completar Parte Diario Maquinaria #{machine_id}",
                description="No se ha registrado actividad para hoy.",
                priority="High",
                form_type="daily_log",
                entity_id=machine_id,
                entity_type="MACHINE",
                payload={'machine_id': machine_id}
            )
            task.priority_order = 1  # Alta prioridad para partes diarios
            return [task]
        return []
    
    def _is_task_allowed_for_role(self, task_config: Dict[str, Any], user_role: str) -> bool:
        """
        Verifica si una tarea está permitida para un rol específico.
        
        Args:
            task_config: Configuración de la tarea del validator_map
            user_role: Rol del usuario actual
            
        Returns:
            True si el rol puede ver/completar esta tarea
        """
        allowed_roles = task_config.get('allowed_roles', [])
        return user_role in allowed_roles if allowed_roles else True
    
    def _get_assigned_machines(self, user_id: int) -> List[int]:
        """
        Obtiene las máquinas asignadas a un usuario.
        
        Por ahora es un mock que retorna [1] para pruebas.
        En producción, consultaría una tabla de asignaciones:
        SELECT machine_id FROM machine_assignments WHERE operator_id = user_id AND active = 1
        
        Args:
            user_id: ID del usuario operador
            
        Returns:
            Lista de IDs de máquinas asignadas
        """
        # TODO: Implementar query real cuando exista tabla machine_assignments
        # Por ahora, mock para pruebas
        return [1]  # Machine ID 1 asignada por defecto

from typing import Optional
from datetime import datetime
from services.common.event_bus import Event, EventTypes
from database.db_manager import DatabaseManager
from domain.maintenance.repositories.maintenance_repository import MaintenancePlanRepository, MaintenanceOrderRepository
from domain.maintenance.entities.maintenance_plan import MaintenanceOrder, MaintenanceStrategy
from domain.logistics.entities.vehicle import Vehicle
from database.repository import BaseRepository

class MaintenanceListener:
    """
    Escucha eventos operativos y gestiona el mantenimiento preventivo.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.plan_repo = MaintenancePlanRepository(db_manager)
        self.order_repo = MaintenanceOrderRepository(db_manager)
        self.vehicle_repo = BaseRepository(db_manager, Vehicle, "vehicles")
    
    def handle_load_completed(self, event: Event) -> None:
        """
        Maneja evento LoadStatusChanged (solo si es COMPLETED).
        Actualiza odómetro de camiones y verifica planes BY_KM.
        """
        if event.data.get('to_status') != 'COMPLETED':
            return
            
        load_id = event.data.get('load_id')
        # Nota: Idealmente el evento traería vehicle_id y distancia recorrida.
        # Por ahora asumiremos que debemos consultar la carga o que el evento evoluciona.
        # Para simplificar y no acoplar, consultaremos el vehículo si viene en data,
        # o asumiremos que el evento se enriquecerá.
        
        # En una implementación real robusta, el evento debería traer:
        # vehicle_id, distance_km (si aplica)
        
        # Simularemos lógica de extracción de datos del evento (o consulta mínima)
        # TODO: Enriquecer evento LoadStatusChanged con vehicle_id y distance
        pass 

    def handle_machine_work(self, event: Event) -> None:
        """
        Maneja evento MachineWorkRecorded.
        Actualiza horómetro y verifica planes BY_HOURS.
        """
        machine_id = event.data.get('machine_id')
        total_hours = event.data.get('total_hours', 0)
        
        if not machine_id:
            return

        self._update_meter_and_check_plans(
            asset_id=machine_id,
            increment=total_hours,
            strategy=MaintenanceStrategy.BY_HOURS
        )

    def _update_meter_and_check_plans(self, asset_id: int, increment: float, strategy: MaintenanceStrategy):
        """
        Lógica central: Actualiza contador y verifica planes.
        """
        vehicle = self.vehicle_repo.get_by_id(asset_id)
        if not vehicle:
            return
            
        # 1. Actualizar contador en vehículo
        current_val = 0.0
        if strategy == MaintenanceStrategy.BY_HOURS:
            current_val = (vehicle.current_hourmeter or 0.0) + increment
            vehicle.current_hourmeter = current_val
        elif strategy == MaintenanceStrategy.BY_KM:
            current_val = (vehicle.current_odometer or 0.0) + increment
            vehicle.current_odometer = current_val
            
        self.vehicle_repo.update(vehicle)
        
        # 2. Verificar planes activos
        plans = self.plan_repo.get_active_plans_by_asset(asset_id)
        for plan in plans:
            if plan.strategy != strategy:
                continue
                
            # Calcular próximo servicio
            next_service_at = plan.last_service_at_meter + plan.frequency_value
            
            if current_val >= next_service_at:
                # Verificar si ya existe orden pendiente para no duplicar
                pending = self.order_repo.get_pending_orders(asset_id)
                # Simplificación: si hay alguna pendiente de este plan, no crear otra
                if any(o.plan_id == plan.id for o in pending):
                    continue
                    
                # Crear Orden de Mantenimiento
                order = MaintenanceOrder(
                    id=None,
                    plan_id=plan.id,
                    asset_id=asset_id,
                    status="PENDING",
                    due_at_meter=next_service_at,
                    generated_at=datetime.now(),
                    notes=f"Generado automáticamente. Contador actual: {current_val}"
                )
                self.order_repo.add(order)
                print(f"🔧 Mantenimiento generado para Activo {asset_id}: {plan.maintenance_type}")

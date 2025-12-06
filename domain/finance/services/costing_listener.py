from datetime import datetime
from infrastructure.events.event_bus import Event
from infrastructure.persistence.database_manager import DatabaseManager
from domain.finance.repositories.finance_repository import RateSheetRepository, CostRecordRepository
from domain.finance.entities.finance_entities import CostRecord
from domain.logistics.repositories.load_repository import LoadRepository

class CostingListener:
    """
    Calcula costos operativos en tiempo real.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.rate_repo = RateSheetRepository(db_manager)
        self.cost_repo = CostRecordRepository(db_manager)
        self.load_repo = LoadRepository(db_manager)
    
    def handle_load_completed(self, event: Event) -> None:
        """
        Calcula costo de transporte al completar carga.
        """
        if event.data.get('to_status') != 'COMPLETED':
            return
            
        load_id = event.data.get('load_id')
        load = self.load_repo.get_by_id(load_id)
        if not load:
            return
            
        # 1. Buscar Tarifa Transporte
        # Asumimos que el cliente dueño de la carga paga (o tarifa base)
        # TODO: Obtener client_id real desde load->contractor o load->origin
        client_id = None 
        rate = self.rate_repo.get_rate('TRANSPORTE', client_id)
        
        if not rate:
            print(f"⚠️ Finance: No rate found for TRANSPORTE")
            return
            
        # 2. Calcular
        amount = 0.0
        if rate.unit_type == 'POR_KM':
            # Mock distance, idealmente viene de load.attributes o ruta
            distance = 50.0 
            amount = distance * rate.unit_price
        elif rate.unit_type == 'POR_TON':
            weight = load.net_weight or 0.0
            amount = weight * rate.unit_price
            
        # 3. Guardar
        self._save_cost(load_id, 'LOAD', amount, rate.id)

    def handle_machine_work(self, event: Event) -> None:
        """
        Calcula costo de maquinaria.
        """
        log_id = event.data.get('log_id')
        total_hours = event.data.get('total_hours', 0.0)
        
        # Buscar tarifa
        rate = self.rate_repo.get_rate('MAQUINARIA')
        if not rate:
            return
            
        amount = total_hours * rate.unit_price
        self._save_cost(log_id, 'MACHINE_LOG', amount, rate.id)

    def _save_cost(self, entity_id: int, entity_type: str, amount: float, rate_id: int):
        record = CostRecord(
            id=None,
            related_entity_id=entity_id,
            related_entity_type=entity_type,
            amount=amount,
            currency='CLP',
            calculated_at=datetime.now(),
            rate_sheet_id=rate_id
        )
        self.cost_repo.add(record)
        print(f"💰 Costo calculado para {entity_type} {entity_id}: ${amount}")

"""
StatusTransitionRepository - Gestión del historial de transiciones de estado

Proporciona operaciones CRUD para el registro de transiciones entre estados
de las cargas, permitiendo auditoría completa y cálculo de SLA.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from infrastructure.persistence.generic_repository import BaseRepository
from domain.logistics.entities.status_transition import StatusTransition
from infrastructure.persistence.database_manager import DatabaseManager


class StatusTransitionRepository(BaseRepository[StatusTransition]):
    """
    Repositorio para gestionar transiciones de estado de cargas.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, StatusTransition, "load_status_history")
    
    def get_by_load_id(self, load_id: int) -> List[StatusTransition]:
        """
        Obtiene todas las transiciones de una carga específica, ordenadas cronológicamente.
        
        Args:
            load_id: ID de la carga
            
        Returns:
            Lista de transiciones ordenadas por timestamp ASC
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE load_id = ? ORDER BY timestamp ASC",
                (load_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_latest_transition(self, load_id: int) -> Optional[StatusTransition]:
        """
        Obtiene la transición más reciente de una carga.
        
        Args:
            load_id: ID de la carga
            
        Returns:
            StatusTransition más reciente o None si no hay historial
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE load_id = ? ORDER BY timestamp DESC LIMIT 1",
                (load_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(dict(row)) if row else None
    
    def get_time_in_status(self, load_id: int, status: str) -> Optional[timedelta]:
        """
        Calcula el tiempo total que una carga estuvo en un estado específico.
        
        Args:
            load_id: ID de la carga
            status: Estado a medir
            
        Returns:
            timedelta con la duración total en ese estado, o None si nunca estuvo
        """
        transitions = self.get_by_load_id(load_id)
        
        total_duration = timedelta()
        entry_time = None
        
        for transition in transitions:
            # Detectar entrada al estado
            if transition.to_status == status:
                entry_time = transition.timestamp
            
            # Detectar salida del estado
            elif transition.from_status == status and entry_time:
                total_duration += transition.timestamp - entry_time
                entry_time = None
        
        # Si aún está en el estado, contar hasta ahora
        if entry_time:
            total_duration += datetime.now() - entry_time
        
        return total_duration if total_duration.total_seconds() > 0 else None
    
    def get_transitions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        to_status: Optional[str] = None
    ) -> List[StatusTransition]:
        """
        Obtiene transiciones dentro de un rango de fechas, opcionalmente filtradas por estado destino.
        
        Útil para reportes de SLA y análisis de rendimiento.
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            to_status: Estado destino opcional para filtrar
            
        Returns:
            Lista de transiciones en el rango
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {self.table_name} WHERE timestamp BETWEEN ? AND ?"
            params = [start_date, end_date]
            
            if to_status:
                query += " AND to_status = ?"
                params.append(to_status)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def _map_row_to_model(self, row: dict) -> StatusTransition:
        """
        Override para manejar conversión de timestamp desde SQLite.
        """
        data = dict(row)
        
        # Convertir timestamp si viene como string
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                pass
        
        return super()._map_row_to_model(data)

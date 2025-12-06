from typing import Optional, List
from infrastructure.persistence.generic_repository import BaseRepository
from domain.agronomy.entities.machine_log import MachineLog
from infrastructure.persistence.database_manager import DatabaseManager


class MachineLogRepository(BaseRepository[MachineLog]):
    """
    Repositorio para gestionar registros de trabajo de maquinaria pesada.
    
    Proporciona operaciones CRUD y consultas específicas para logs de máquinas.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, MachineLog, "machine_logs")
    
    def get_latest_log_by_machine(self, machine_id: int) -> Optional[MachineLog]:
        """
        Obtiene el último registro de trabajo de una máquina.
        
        Crítico para validación de continuidad de horómetros.
        
        Args:
            machine_id: ID de la máquina
            
        Returns:
            MachineLog más reciente o None si no hay registros
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE machine_id = ? 
                    ORDER BY date DESC, end_hourmeter DESC 
                    LIMIT 1""",
                (machine_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(dict(row)) if row else None
    
    def get_by_machine_id(self, machine_id: int) -> List[MachineLog]:
        """
        Obtiene todos los registros de trabajo de una máquina.
        
        Args:
            machine_id: ID de la máquina
            
        Returns:
            Lista de logs ordenados por fecha descendente
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE machine_id = ? 
                    ORDER BY date DESC""",
                (machine_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]
    
    def get_by_site_id(self, site_id: int) -> List[MachineLog]:
        """
        Obtiene todos los registros de trabajo en un sitio.
        
        Args:
            site_id: ID del sitio
            
        Returns:
            Lista de logs ordenados por fecha descendente
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name} 
                    WHERE site_id = ? 
                    ORDER BY date DESC""",
                (site_id,)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

from typing import List, Optional
from datetime import datetime
from database.repository import BaseRepository
from models.operations.load import Load
from database.db_manager import DatabaseManager

class LoadRepository(BaseRepository[Load]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, Load, "loads")

    def _map_row_to_model(self, row: dict) -> Load:
        """
        Override to handle datetime conversion from SQLite strings.
        """
        data = dict(row)
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at', 'dispatch_time', 'arrival_time', 'completion_time']
        for field in datetime_fields:
            if field in data and isinstance(data[field], str):
                try:
                    # Handle format "YYYY-MM-DD HH:MM:SS.ssssss" or "YYYY-MM-DD HH:MM:SS"
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    # Fallback or log error
                    pass
                    
        return super()._map_row_to_model(data)

    def get_next_manifest_sequence(self) -> int:
        """
        Returns the next sequence number using the sequences table.
        Thread-safe implementation using atomic update.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            # Atomic update
            cursor.execute("UPDATE sequences SET current_value = current_value + 1 WHERE name = 'manifest_code'")
            
            # If no row updated (should not happen if migration ran), insert it
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO sequences (name, current_value) VALUES ('manifest_code', 1)")
                return 1
                
            # Retrieve the new value
            cursor.execute("SELECT current_value FROM sequences WHERE name = 'manifest_code'")
            row = cursor.fetchone()
            return row['current_value'] if row else 1

    def get_all(self, limit: int = 50, offset: int = 0) -> List[Load]:
        """
        Get all loads with pagination.
        Overrides BaseRepository.get_all to enforce limits.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_active_loads(self) -> List[Load]:
        """
        Returns all loads that are NOT 'COMPLETED' or 'CANCELLED'.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status NOT IN ('COMPLETED', 'CANCELLED') ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_status(self, status: str, limit: int = 50) -> List[Load]:
        """
        Returns loads filtered by status, ordered by created_at DESC.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC LIMIT ?", 
                (status, limit)
            )
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]


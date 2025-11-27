from typing import TypeVar, Generic, List, Optional, Type, Any
from database.db_manager import DatabaseManager
from dataclasses import fields

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, db_manager: DatabaseManager, model_cls: Type[T], table_name: str):
        self.db_manager = db_manager
        self.model_cls = model_cls
        self.table_name = table_name

    def get_all(self, order_by: str = "id") -> List[T]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY {order_by}")
            rows = cursor.fetchall()
            return [self.model_cls(**dict(row)) for row in rows]

    def get_by_id(self, id: int) -> Optional[T]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                return self.model_cls(**dict(row))
            return None

    def add(self, entity: T) -> T:
        # Dynamically build INSERT query based on dataclass fields
        # Exclude 'id' and 'created_at' usually, but let's be generic.
        # We assume 'id' is None for new entities and auto-incremented.
        
        entity_fields = [f.name for f in fields(entity) if f.name != 'id' and getattr(entity, f.name) is not None]
        placeholders = ", ".join(["?"] * len(entity_fields))
        columns = ", ".join(entity_fields)
        values = [getattr(entity, f) for f in entity_fields]
        
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            entity.id = cursor.lastrowid
            return entity

    def update(self, entity: T) -> bool:
        if not entity.id:
            return False
            
        entity_fields = [f.name for f in fields(entity) if f.name != 'id' and getattr(entity, f.name) is not None]
        set_clause = ", ".join([f"{field} = ?" for field in entity_fields])
        values = [getattr(entity, f) for f in entity_fields]
        values.append(entity.id)
        
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
            return cursor.rowcount > 0

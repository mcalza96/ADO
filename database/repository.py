from typing import TypeVar, Generic, List, Optional, Type, Any
from database.db_manager import DatabaseManager
from dataclasses import fields
import sqlite3

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Base repository implementing the Repository Pattern with support for:
    - Soft Delete (is_active flag)
    - Audit trail (updated_at timestamp)
    - Generic CRUD operations
    """
    
    def __init__(self, db_manager: DatabaseManager, model_cls: Type[T], table_name: str):
        self.db_manager = db_manager
        self.model_cls = model_cls
        self.table_name = table_name

    def _map_row_to_model(self, row: dict) -> T:
        """
        Maps a database row dictionary to the model class, filtering out
        any keys that don't exist in the model's fields.
        """
        model_fields = {f.name for f in fields(self.model_cls)}
        filtered_data = {k: v for k, v in row.items() if k in model_fields}
        return self.model_cls(**filtered_data)

    def get_all(self, active_only: bool = True, order_by: str = "id") -> List[T]:
        """
        Get all records from the table.
        
        Args:
            active_only: If True, only return records where is_active=1
            order_by: Column to order results by
            
        Returns:
            List of model instances
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            
            # Check if table has is_active column
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            has_is_active = 'is_active' in columns
            
            if has_is_active and active_only:
                query = f"SELECT * FROM {self.table_name} WHERE is_active = 1 ORDER BY {order_by}"
            else:
                query = f"SELECT * FROM {self.table_name} ORDER BY {order_by}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get a single record by ID.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None

    def add(self, entity: T) -> T:
        """
        Create a new record.
        
        Args:
            entity: Model instance to insert
            
        Returns:
            The same entity with populated ID
        """
        # Get table columns to filter out relationship fields
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            # row[1] is column name
            table_columns = {row[1] for row in cursor.fetchall()}

        # Dynamically build INSERT query based on dataclass fields
        # Exclude 'id', 'created_at', 'updated_at' as they're auto-generated
        # And exclude fields that are not in the table (like relationships)
        entity_fields = [
            f.name for f in fields(entity) 
            if f.name not in ('id', 'created_at', 'updated_at') 
            and f.name in table_columns
            and getattr(entity, f.name) is not None
        ]
        
        placeholders = ", ".join(["?"] * len(entity_fields))
        columns = ", ".join(entity_fields)
        values = [getattr(entity, f) for f in entity_fields]
        
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(values))
                entity.id = cursor.lastrowid
                return entity
        except sqlite3.Error as e:
            raise Exception(f"Error creating {self.table_name} record: {str(e)}")

    def update(self, entity: T) -> bool:
        """
        Update an existing record.
        Automatically sets updated_at to CURRENT_TIMESTAMP.
        
        Args:
            entity: Model instance with ID to update
            
        Returns:
            True if record was updated, False otherwise
        """
        if not entity.id:
            return False
        
        # Get table columns
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            table_columns = {row[1] for row in cursor.fetchall()}
        
        # Get all fields except id, created_at, and updated_at
        # And ensure they exist in table
        entity_fields = [
            f.name for f in fields(entity) 
            if f.name not in ('id', 'created_at', 'updated_at') 
            and f.name in table_columns
            and getattr(entity, f.name) is not None
        ]
        
        # Build SET clause
        set_parts = [f"{field} = ?" for field in entity_fields]
        
        if 'updated_at' in table_columns:
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
        
        set_clause = ", ".join(set_parts)
        values = [getattr(entity, f) for f in entity_fields]
        values.append(entity.id)
        
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(values))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise Exception(f"Error updating {self.table_name} record: {str(e)}")

    def delete(self, id: int) -> bool:
        """
        Soft delete a record by setting is_active = 0.
        If the table doesn't have is_active column, performs hard delete.
        
        Args:
            id: Primary key value
            
        Returns:
            True if record was deleted/deactivated, False otherwise
        """
        # Check if table has is_active column
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            has_is_active = 'is_active' in columns
            
            try:
                if has_is_active:
                    # Soft delete: set is_active = 0
                    # Also update updated_at if it exists
                    if 'updated_at' in columns:
                        query = f"UPDATE {self.table_name} SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
                    else:
                        query = f"UPDATE {self.table_name} SET is_active = 0 WHERE id = ?"
                else:
                    # Hard delete as fallback
                    query = f"DELETE FROM {self.table_name} WHERE id = ?"
                
                cursor.execute(query, (id,))
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                raise Exception(f"Error deleting {self.table_name} record: {str(e)}")

    def get_by_attribute(self, attribute: str, value: Any) -> Optional[T]:
        """
        Get a single record by a specific attribute.
        
        Args:
            attribute: Column name to filter by
            value: Value to match
            
        Returns:
            Model instance or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {attribute} = ?", (value,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_model(dict(row))
            return None

    def get_all_filtered(self, **kwargs) -> List[T]:
        """
        Get all records matching the given filters.
        Example: repo.get_all_filtered(contractor_id=1, is_active=1)
        
        Args:
            **kwargs: Column names and values to filter by
            
        Returns:
            List of model instances
        """
        if not kwargs:
            return self.get_all()
            
        conditions = [f"{key} = ?" for key in kwargs.keys()]
        where_clause = " AND ".join(conditions)
        values = list(kwargs.values())
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where_clause}", tuple(values))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

from typing import List, Optional, Type, TypeVar, Any
from database.db_manager import DatabaseManager

T = TypeVar('T')

class BaseService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[Any]]:
        """
        Executes a read query and returns the results.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """
        Executes a write query (INSERT, UPDATE, DELETE) and returns the last row id or row count.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

from typing import List, Optional, Type, TypeVar, Any
from database.db_manager import DatabaseManager

T = TypeVar('T')

class BaseService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    # Methods execute_query and execute_non_query have been removed to enforce Repository Pattern usage.


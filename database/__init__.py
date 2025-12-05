"""
Database Module - Gestión de persistencia.

Exporta el manager de base de datos y el repositorio base.
"""

from .db_manager import DatabaseManager
from .repository import BaseRepository

__all__ = ['DatabaseManager', 'BaseRepository']
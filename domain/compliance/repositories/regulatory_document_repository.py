from typing import Optional
from database.repository import BaseRepository
from domain.compliance.entities.regulatory_document import RegulatoryDocument
from database.db_manager import DatabaseManager

class RegulatoryDocumentRepository(BaseRepository[RegulatoryDocument]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, RegulatoryDocument, "regulatory_documents")
    
    def get_by_load_id(self, load_id: int) -> Optional[RegulatoryDocument]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE related_load_id = ?",
                (load_id,)
            )
            row = cursor.fetchone()
            return self._map_row_to_model(dict(row)) if row else None

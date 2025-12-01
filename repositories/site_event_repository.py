from typing import List
from database.repository import BaseRepository
from models.operations.site_event import SiteEvent
from database.db_manager import DatabaseManager

class SiteEventRepository(BaseRepository[SiteEvent]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, SiteEvent, "site_events")

    def get_by_site_id(self, site_id: int) -> List[SiteEvent]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM site_events WHERE site_id = ? ORDER BY event_date DESC", (site_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_model(dict(row)) for row in rows]

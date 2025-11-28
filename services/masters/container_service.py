from typing import List, Optional
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.container import Container

class ContainerService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.repo = BaseRepository(db_manager, Container, "containers")

    def create_container(self, code: str, plant_id: Optional[int] = None) -> Container:
        container = Container(id=None, code=code, status='AVAILABLE', current_plant_id=plant_id)
        return self.repo.add(container)

    def get_all_containers(self) -> List[Container]:
        return self.repo.get_all()

    def get_available_containers(self, plant_id: Optional[int] = None) -> List[Container]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            if plant_id:
                cursor.execute("SELECT * FROM containers WHERE status = 'AVAILABLE' AND (current_plant_id = ? OR current_plant_id IS NULL)", (plant_id,))
            else:
                cursor.execute("SELECT * FROM containers WHERE status = 'AVAILABLE'")
            rows = cursor.fetchall()
            return [Container(**dict(row)) for row in rows]
            
    def get_ready_containers(self, plant_id: int) -> List[Container]:
        """
        Returns containers that are associated with a READY TreatmentBatch at the given plant.
        This is a bit complex because the container status is IN_USE until dispatched, 
        but logically it is 'Ready for Pickup' if the batch is READY.
        """
        # Actually, the container status remains IN_USE until it leaves the plant.
        # But for the UI selector in Planning, we need to find containers that are holding a READY batch.
        with self.db_manager as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.* 
                FROM containers c
                JOIN treatment_batches tb ON c.id = tb.container_id
                WHERE tb.plant_id = ? 
                AND tb.status = 'READY'
                AND c.status = 'IN_USE'
            """
            cursor.execute(query, (plant_id,))
            rows = cursor.fetchall()
            return [Container(**dict(row)) for row in rows]

    def update_status(self, container_id: int, new_status: str):
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE containers SET status = ? WHERE id = ?", (new_status, container_id))
            conn.commit()

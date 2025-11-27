from typing import List
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
from models.masters.client import Client

class ClientService:
    def __init__(self, db_manager: DatabaseManager):
        self.repository = BaseRepository(db_manager, Client, "clients")

    def get_all_clients(self) -> List[Client]:
        return self.repository.get_all(order_by="name")

    def create_client(self, client: Client) -> Client:
        # Add validation logic here if needed
        return self.repository.add(client)

    def update_client(self, client: Client) -> bool:
        return self.repository.update(client)

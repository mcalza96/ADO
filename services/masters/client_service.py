from typing import List, Optional
from database.db_manager import DatabaseManager
from repositories.client_repository import ClientRepository
from models.masters.client import Client


class ClientService:
    def __init__(self, db_manager: DatabaseManager):
        self.repository = ClientRepository(db_manager)

    def get_all_clients(self) -> List[Client]:
        return self.repository.get_all_ordered()

    def create_client(self, client: Client) -> Client:
        # Add validation logic here if needed
        return self.repository.add(client)

    def update_client(self, client: Client) -> bool:
        return self.repository.update(client)
    
    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        return self.repository.get_by_id(client_id)


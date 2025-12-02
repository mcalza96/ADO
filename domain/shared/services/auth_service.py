from typing import Optional
from domain.shared.base_service import BaseService
from database.repository import BaseRepository
from domain.shared.entities.user import User
import hashlib

class AuthService(BaseService):
    def __init__(self, user_repo: BaseRepository[User]):
        self.user_repository = user_repo

    def create_user(self, user: User) -> User:
        """
        Creates a new user with hashed password.
        """
        # Hash password before saving
        if user.password_hash:
            user.password_hash = hashlib.sha256(user.password_hash.encode()).hexdigest()
        
        return self.user_repository.add(user)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username.
        """
        return self.user_repository.get_by_attribute("username", username)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user by username and password.
        """
        user = self.get_user_by_username(username)
        if user and user.password_hash:
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            if input_hash == user.password_hash:
                return user
        return None

from typing import Optional
from services.base_service import BaseService
from database.repository import BaseRepository
from models.auth.user import User
import hashlib

class AuthService(BaseService):
    def __init__(self, user_repo: BaseRepository[User]):
        self.user_repository = user_repo

    def create_user(self, user: User) -> User:
        """
        Creates a new user with hashed password.
        """
        # Simple hashing for demo purposes
        pwd_hash = hashlib.sha256(user.password_hash.encode()).hexdigest() if user.password_hash else ""
        
        return self.user_repository.create(user, pwd_hash)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user by username.
        """
        return self.user_repository.get_by_username(username)

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

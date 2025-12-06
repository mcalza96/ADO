from typing import Optional, List
from domain.shared.base_service import BaseService
from infrastructure.persistence.generic_repository import BaseRepository
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
    
    def get_all_users(self) -> List[User]:
        """Returns all users."""
        return self.user_repository.get_all()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Returns user by ID."""
        return self.user_repository.get_by_id(user_id)

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
    
    def update_user(self, user: User) -> bool:
        """Updates user data (except password)."""
        return self.user_repository.update(user)
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Changes user password."""
        user = self.user_repository.get_by_id(user_id)
        if user:
            user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            return self.user_repository.update(user)
        return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivates a user."""
        user = self.user_repository.get_by_id(user_id)
        if user:
            user.is_active = False
            return self.user_repository.update(user)
        return False
    
    def activate_user(self, user_id: int) -> bool:
        """Activates a user."""
        user = self.user_repository.get_by_id(user_id)
        if user:
            user.is_active = True
            return self.user_repository.update(user)
        return False

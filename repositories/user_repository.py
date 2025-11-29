from typing import Optional
from database.repository import BaseRepository
from models.auth.user import User
from database.db_manager import DatabaseManager

class UserRepository(BaseRepository[User]):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager, User, "users")

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Returns a user by username.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return self.model_cls(**dict(row))
            return None

    def create(self, user: User, password_hash: str) -> User:
        """
        Creates a new user with the given password hash.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""INSERT INTO {self.table_name} (username, email, password_hash, full_name, role, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user.username, user.email, password_hash, user.full_name, user.role, user.is_active)
            )
            user.id = cursor.lastrowid
            return user

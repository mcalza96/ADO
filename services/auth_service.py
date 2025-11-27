from typing import Optional
from services.base_service import BaseService
from models.auth.user import User
import hashlib

class AuthService(BaseService):
    def create_user(self, user: User) -> User:
        query = """
            INSERT INTO users (username, email, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        # Simple hashing for demo purposes
        pwd_hash = hashlib.sha256(user.password_hash.encode()).hexdigest() if user.password_hash else ""
        
        user_id = self.execute_non_query(
            query, 
            (user.username, user.email, pwd_hash, user.full_name, user.role, user.is_active)
        )
        user.id = user_id
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        query = "SELECT * FROM users WHERE username = ?"
        rows = self.execute_query(query, (username,))
        
        if rows and len(rows) > 0:
            row = rows[0]
            # Convert sqlite3.Row to User object
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                role=row['role'],
                password_hash=row['password_hash'],
                created_at=row['created_at'],
                is_active=bool(row['is_active'])
            )
        return None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if user and user.password_hash:
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            if input_hash == user.password_hash:
                return user
        return None

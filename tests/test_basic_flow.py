from database.db_manager import DatabaseManager
from services.auth_service import AuthService
from models.core import User

def test_flow():
    db = DatabaseManager()
    auth_service = AuthService(db)

    print("--- Testing User Creation ---")
    new_user = User(
        id=None,
        username="admin_test",
        email="admin@test.com",
        full_name="Admin User",
        role="Admin",
        password_hash="secret123"
    )
    
    try:
        created_user = auth_service.create_user(new_user)
        print(f"User created with ID: {created_user.id}")
    except Exception as e:
        print(f"Error creating user (might already exist): {e}")

    print("\n--- Testing Authentication ---")
    user = auth_service.authenticate("admin_test", "secret123")
    if user:
        print(f"Authentication Successful for: {user.full_name} ({user.role})")
    else:
        print("Authentication Failed")

    print("\n--- Testing Invalid Login ---")
    user_fail = auth_service.authenticate("admin_test", "wrongpass")
    if user_fail:
        print("Authentication Successful (Unexpected)")
    else:
        print("Authentication Failed (Expected)")

if __name__ == "__main__":
    test_flow()

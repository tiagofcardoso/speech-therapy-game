from database.db_connector import DatabaseConnector
import hashlib
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_test_user():
    """Create a test user in the database"""
    db = DatabaseConnector()
    
    # Check if user already exists
    if db.get_user_by_username("test@example.com"):
        print("Test user already exists")
        return
    
    # Create user with hashed password
    salt = uuid.uuid4().hex
    password = "password123"
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    
    user = {
        "username": "test@example.com",
        "password": hashed_password,
        "salt": salt,
        "name": "Test User",
        "age": 8,
        "history": []
    }
    
    user_id = db.save_user(user)
    print(f"Created test user with ID: {user_id}")
    print(f"Username: test@example.com")
    print(f"Password: password123")

if __name__ == "__main__":
    create_test_user()
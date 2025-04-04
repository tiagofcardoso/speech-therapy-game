import os
import jwt
import datetime
import hashlib
import uuid
from typing import Dict, Any, Optional

from database.db_connector import DatabaseConnector
from config import JWT_SECRET_KEY

class AuthService:
    def __init__(self):
        """Initialize auth service with database connector"""
        self.db = DatabaseConnector()
        self.jwt_secret = JWT_SECRET_KEY
        self.token_expiry = 60 * 60 * 24 * 7  # 7 days in seconds
    
    def register_user(self, username: str, password: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user
        
        Parameters:
        username (str): Username
        password (str): Password
        profile_data (Dict): User profile data
        
        Returns:
        Dict: Registration result with user ID and token
        """
        # Check if username already exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            return {"success": False, "message": "Username already exists"}
        
        # Hash password
        salt = uuid.uuid4().hex
        hashed_password = self._hash_password(password, salt)
        
        # Create user object
        user = {
            "username": username,
            "password": hashed_password,
            "salt": salt,
            "created_at": datetime.datetime.now(),
            "name": profile_data.get("name", ""),
            "age": profile_data.get("age", 0),
            "history": []
        }
        
        # Save user
        user_id = self.db.save_user(user)
        if hasattr(user_id, '__str__'):
            user_id = str(user_id)

        # Generate token
        token = self._generate_token(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "token": token
        }
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login
        
        Parameters:
        username (str): Username
        password (str): Password
        
        Returns:
        Dict: Login result with user ID and token
        """
        user = self.db.get_user_by_username(username)
        if not user:
            return {"success": False, "message": "Invalid username or password"}
        
        # Verify password
        hashed_password = self._hash_password(password, user.get("salt", ""))
        if hashed_password != user.get("password"):
            return {"success": False, "message": "Invalid username or password"}
        
        # Get user ID and convert to string if it's an ObjectId
        user_id = user.get("_id")
        if hasattr(user_id, '__str__'):
            user_id_str = str(user_id)
        else:
            user_id_str = user_id
        
        # Generate token
        token = self._generate_token(user_id)
        
        return {
            "success": True,
            "user_id": user_id_str,  # Use string version here
            "token": token,
            "name": user.get("name")
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token
        
        Parameters:
        token (str): JWT token
        
        Returns:
        Dict: Verification result with user ID if valid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return {"valid": True, "user_id": payload.get("user_id")}
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return {"valid": False}
    
    def _generate_token(self, user_id):
        # Converter ObjectId para string antes de usar no JWT
        if hasattr(user_id, '__str__'):
            user_id = str(user_id)
        
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
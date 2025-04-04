import os
import pymongo
from pymongo import MongoClient
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import MONGODB_URI

logger = logging.getLogger(__name__)

class DatabaseConnector:
    def __init__(self):
        """Initialize database connection with fallback to in-memory mode"""
        self.in_memory_db = {}
        self.connected = False
        
        try:
            # Try to connect to MongoDB
            self.client = MongoClient(MONGODB_URI, 
                                     serverSelectionTimeoutMS=5000,
                                     connectTimeoutMS=5000,
                                     socketTimeoutMS=5000)
            self.client.admin.command('ping')  # Check connection
            self.db = self.client.get_database()
            self.connected = True
            print("Connected to MongoDB successfully")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            print("Using in-memory database instead")
            self.connected = False
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if self.connected:
            return self.db.users.find_one({"_id": user_id})
        return self.in_memory_db.get("users", {}).get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        if self.connected:
            return self.db.users.find_one({"username": username})
        
        # In-memory lookup
        users = self.in_memory_db.get("users", {}).values()
        for user in users:
            if user.get("username") == username:
                return user
        return None
    
    def save_user(self, user: Dict[str, Any]) -> str:
        """Save user data and return user ID"""
        if self.connected:
            if "_id" not in user:
                result = self.db.users.insert_one(user)
                return str(result.inserted_id)
            else:
                self.db.users.replace_one({"_id": user["_id"]}, user, upsert=True)
                return user["_id"]
        
        # In-memory save
        if "users" not in self.in_memory_db:
            self.in_memory_db["users"] = {}
        
        if "_id" not in user:
            user["_id"] = str(uuid.uuid4())
        
        self.in_memory_db["users"][user["_id"]] = user
        return user["_id"]
    
    def save_session(self, session: Dict[str, Any]) -> str:
        """Save game session"""
        if self.connected:
            if "_id" not in session:
                result = self.db.sessions.insert_one(session)
                return str(result.inserted_id)
            else:
                self.db.sessions.replace_one({"_id": session["_id"]}, session, upsert=True)
                return session["_id"]
        
        # In-memory save
        if "sessions" not in self.in_memory_db:
            self.in_memory_db["sessions"] = {}
        
        session_id = session.get("session_id", str(uuid.uuid4()))
        self.in_memory_db["sessions"][session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        if self.connected:
            return self.db.sessions.find_one({"session_id": session_id})
        return self.in_memory_db.get("sessions", {}).get(session_id)
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent sessions"""
        if self.connected:
            cursor = self.db.sessions.find({"user_id": user_id}).sort("start_time", -1).limit(limit)
            return list(cursor)
        
        # In-memory query
        sessions = self.in_memory_db.get("sessions", {}).values()
        user_sessions = [s for s in sessions if s.get("user_id") == user_id]
        return sorted(user_sessions, key=lambda x: x.get("start_time", 0), reverse=True)[:limit]
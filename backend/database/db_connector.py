import os
import pymongo
from pymongo import MongoClient
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from config import MONGODB_URI
from bson.objectid import ObjectId

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
                self.db.users.replace_one(
                    {"_id": user["_id"]}, user, upsert=True)
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
                self.db.sessions.replace_one(
                    {"_id": session["_id"]}, session, upsert=True)
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
            cursor = self.db.sessions.find({"user_id": user_id}).sort(
                "start_time", -1).limit(limit)
            return list(cursor)

        # In-memory query
        sessions = self.in_memory_db.get("sessions", {}).values()
        user_sessions = [s for s in sessions if s.get("user_id") == user_id]
        return sorted(user_sessions, key=lambda x: x.get("start_time", 0), reverse=True)[:limit]

    def user_exists(self, username):
        """
        Verifica se um usuário com o username fornecido já existe
        """
        try:
            # Verifique separadamente para identificar o tipo de conflito
            email_exists = self.db.users.find_one(
                {"email": username}) is not None
            username_exists = self.db.users.find_one(
                {"username": username}) is not None

            if email_exists:
                print(f"Usuário com email '{username}' já existe")
            if username_exists:
                print(f"Usuário com username '{username}' já existe")

            return email_exists or username_exists
        except Exception as e:
            print(f"Erro ao verificar se usuário existe: {str(e)}")
            return False

    def create_user(self, user_data):
        """
        Cria um novo usuário no banco de dados

        Args:
            user_data (dict): Dados do usuário (nome, username, senha)

        Returns:
            str: ID do usuário criado
        """
        try:
            from werkzeug.security import generate_password_hash

            # Criar objeto de usuário para inserção
            new_user = {
                "name": user_data.get("name"),
                "username": user_data.get("username"),  # Novo campo username
                # Usar username como email se não fornecido
                "email": user_data.get("email", user_data.get("username")),
                "password": generate_password_hash(user_data.get("password")),
                "created_at": datetime.utcnow(),
                "age": user_data.get("age"),  # Novo campo age
                "statistics": {
                    "exercises_completed": 0,
                    "accuracy": 0,
                    "last_login": datetime.utcnow()
                }
            }

            # Inserir usuário no banco
            result = self.db.users.insert_one(new_user)

            # Retornar o ID do novo usuário
            return result.inserted_id
        except Exception as e:
            print(f"Erro ao criar usuário: {str(e)}")
            raise

    def authenticate_user(self, username, password):
        """
        Autentica um usuário com username e senha

        Args:
            username (str): Username ou email do usuário
            password (str): Senha do usuário

        Returns:
            dict: Dados do usuário se autenticação bem-sucedida, None caso contrário
        """
        try:
            from werkzeug.security import check_password_hash

            # Buscar usuário pelo username (que pode ser email)
            user = self.db.users.find_one({"$or": [
                {"email": username},
                {"username": username}
            ]})

            # Verificar se usuário existe e a senha está correta
            if user and check_password_hash(user["password"], password):
                # Atualizar estatísticas de último login
                self.db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"statistics.last_login": datetime.utcnow()}}
                )
                return user

            return None
        except Exception as e:
            print(f"Erro ao autenticar usuário: {str(e)}")
            return None

    def store_game(self, user_id, game_data):
        """
        Armazena um jogo no banco de dados

        Args:
            user_id (str): ID do usuário
            game_data (dict): Dados do jogo

        Returns:
            str: ID do jogo armazenado
        """
        try:
            # Criar objeto de jogo para inserção
            game = {
                "user_id": user_id,
                "game_type": game_data.get("game_type", "unknown"),
                "difficulty": game_data.get("difficulty", "beginner"),
                "title": game_data.get("title", "Jogo sem título"),
                "content": game_data,
                "created_at": datetime.now(),  # Corrigido!
                "completed": False
            }

            # Inserir jogo no banco
            result = self.db.games.insert_one(game)

            # Retornar o ID do jogo
            return result.inserted_id
        except Exception as e:
            print(f"Erro ao armazenar jogo: {str(e)}")
            raise

    def get_game(self, game_id, user_id=None):
        """
        Get a game by its ID

        Args:
            game_id: The ID of the game to retrieve
            user_id: Optional user ID for access control

        Returns:
            dict: The game data or None if not found
        """
        try:
            # Convert string ID to ObjectId if needed
            if isinstance(game_id, str):
                try:
                    game_id = ObjectId(game_id)
                except:
                    print(f"Invalid game_id format: {game_id}")
                    return None

            # Get the game from the database
            game = self.db.games.find_one({"_id": game_id})

            # Log the result for debugging
            if game:
                print(f"Found game: {game.get('title', 'Untitled')}")
            else:
                print(f"Game not found: {game_id}")

            return game
        except Exception as e:
            print(f"Error retrieving game: {str(e)}")
            return None

    def get_user_games(self, user_id, limit=10):
        """
        Busca jogos de um usuário

        Args:
            user_id (str): ID do usuário
            limit (int): Número máximo de jogos a retornar

        Returns:
            list: Lista de jogos do usuário
        """
        try:
            if self.connected:
                cursor = self.db.games.find({"user_id": user_id}).sort(
                    "created_at", -1).limit(limit)
                return list(cursor)

            # Fallback para armazenamento em memória
            games = self.in_memory_db.get("games", {}).values()
            user_games = [g for g in games if g.get("user_id") == user_id]
            return sorted(user_games, key=lambda x: x.get("created_at", 0), reverse=True)[:limit]

        except Exception as e:
            print(f"Erro ao buscar jogos do usuário: {str(e)}")
            return []

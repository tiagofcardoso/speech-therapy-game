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

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID with proper ObjectId conversion"""
        try:
            # Converter string ID para ObjectId se necessário
            if isinstance(user_id, str):
                try:
                    obj_id = ObjectId(user_id)
                except:
                    print(f"⚠️ Formato de ID de usuário inválido: {user_id}")
                    # Tentar buscar como string diretamente (fallback)
                    if self.connected:
                        user = self.db.users.find_one({"_id": user_id})
                        if user:
                            return user
                    return None
            else:
                obj_id = user_id

            # Buscar usuário pelo ObjectId
            if self.connected:
                user = self.db.users.find_one({"_id": obj_id})
                if user:
                    print(
                        f"✅ Usuário encontrado: {user.get('name', 'Sem nome')}")
                    return user
                else:
                    print(f"❌ Usuário não encontrado com ID: {user_id}")

            # Fallback para busca em memória
            return self.in_memory_db.get("users", {}).get(str(user_id))

        except Exception as e:
            print(f"❌ Erro ao buscar usuário por ID: {str(e)}")
            return None

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

    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Atualiza os dados de uma sessão existente

        Args:
            session_id: ID da sessão a atualizar
            update_data: Dicionário com os campos a atualizar

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            if self.connected:
                # Atualizar no MongoDB
                result = self.db.sessions.update_one(
                    {"session_id": session_id},
                    {"$set": update_data}
                )

                if result.modified_count == 0:
                    print(
                        f"Sessão não encontrada ou sem alterações: {session_id}")
                    return False

                print(f"Sessão atualizada com sucesso: {session_id}")
                return True

            # Fallback para in-memory
            if "sessions" not in self.in_memory_db:
                return False

            if session_id not in self.in_memory_db["sessions"]:
                return False

            # Atualizar no armazenamento em memória
            for key, value in update_data.items():
                self.in_memory_db["sessions"][session_id][key] = value

            return True
        except Exception as e:
            print(f"Erro ao atualizar sessão: {str(e)}")
            return False

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Atualiza dados do usuário com suporte a campos aninhados (dot notation)
        """
        try:
            updates = {}

            # Processar campos com notação de ponto
            for key, value in update_data.items():
                if "." in key:
                    # MongoDB suporta dot notation diretamente
                    updates[key] = value
                else:
                    updates[key] = value

            if self.connected:
                result = self.db.users.update_one(
                    {"_id": user_id},
                    {"$set": updates}
                )
                return result.modified_count > 0

            # Fallback para in-memory
            if "users" not in self.in_memory_db:
                return False

            if user_id not in self.in_memory_db["users"]:
                return False

            # Atualizar no armazenamento in-memory
            for key, value in update_data.items():
                if "." in key:
                    # Processar campos aninhados
                    parts = key.split(".")
                    current = self.in_memory_db["users"][user_id]
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    self.in_memory_db["users"][user_id][key] = value

            return True
        except Exception as e:
            print(f"Erro ao atualizar usuário: {str(e)}")
            return False

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

    def add_to_user_history(self, user_id, session_summary):
        """
        Adiciona uma entrada ao histórico de sessões completas do usuário

        Args:
            user_id: ID do usuário
            session_summary: Resumo da sessão a ser adicionada ao histórico

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            if not user_id or not session_summary:
                print("⚠️ Dados incompletos para adicionar ao histórico")
                return False

            print(
                f"Adicionando ao histórico do usuário {user_id}: {session_summary}")

            if self.connected:
                # Usar $push para adicionar a uma array no MongoDB
                result = self.db.users.update_one(
                    {"_id": ObjectId(user_id) if ObjectId.is_valid(
                        user_id) else user_id},
                    {"$push": {"history.completed_sessions": session_summary}}
                )

                success = result.modified_count > 0
                print(f"Histórico atualizado com sucesso: {success}")
                return success

            # Fallback para in-memory
            user = self.get_user_by_id(user_id)
            if not user:
                print(f"❌ Usuário não encontrado: {user_id}")
                return False

            if "history" not in user:
                user["history"] = {}
            if "completed_sessions" not in user["history"]:
                user["history"]["completed_sessions"] = []

            user["history"]["completed_sessions"].append(session_summary)

            # Salvar usuário atualizado
            self.save_user(user)
            return True

        except Exception as e:
            print(f"❌ Erro ao adicionar ao histórico do usuário: {str(e)}")
            return False

    def update_game(self, game_id, update_data):
        """
        Atualiza os dados de um jogo no banco de dados

        Args:
            game_id: ID do jogo a ser atualizado
            update_data: Dicionário com os campos a atualizar

        Returns:
            bool: True se sucesso, False caso contrário
        """
        try:
            if not game_id:
                print("⚠️ ID do jogo não fornecido para atualização")
                return False

            print(f"Atualizando jogo {game_id} com dados: {update_data}")

            if self.connected:
                # Converter string ID para ObjectId se necessário
                if isinstance(game_id, str):
                    try:
                        obj_id = ObjectId(game_id)
                    except:
                        print(f"⚠️ Formato de ID de jogo inválido: {game_id}")
                        # Vamos tentar buscar diretamente como string
                        result = self.db.games.update_one(
                            {"_id": game_id},
                            {"$set": update_data}
                        )
                        return result.modified_count > 0
                else:
                    obj_id = game_id

                # Atualizar o jogo no MongoDB
                result = self.db.games.update_one(
                    {"_id": obj_id},
                    {"$set": update_data}
                )

                success = result.modified_count > 0
                print(f"Jogo atualizado com sucesso: {success}")
                return success

            # Fallback para in-memory
            if "games" not in self.in_memory_db:
                return False

            # Tentar encontrar o jogo em memória
            game_str_id = str(game_id)
            if game_str_id in self.in_memory_db["games"]:
                # Atualizar cada campo
                for key, value in update_data.items():
                    self.in_memory_db["games"][game_str_id][key] = value
                return True

            return False

        except Exception as e:
            print(f"❌ Erro ao atualizar jogo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_completed_games(self, user_id):
        """
        Busca jogos completos de um usuário diretamente da coleção de jogos

        Args:
            user_id (str): ID do usuário

        Returns:
            list: Lista de jogos completos do usuário
        """
        try:
            print(f"Buscando jogos completos para o usuário: {user_id}")

            if self.connected:
                cursor = self.db.games.find({
                    "user_id": user_id,
                    "completed": True
                }).sort("completed_at", -1)

                games = list(cursor)
                print(f"Encontrados {len(games)} jogos completos")
                return games

            # Fallback para armazenamento em memória
            games = self.in_memory_db.get("games", {}).values()
            completed_games = [
                g for g in games
                if g.get("user_id") == user_id and g.get("completed") == True
            ]

            return completed_games

        except Exception as e:
            print(f"❌ Erro ao buscar jogos completos do usuário: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


# Funções para atender às requisições da API
def get_user_history(user_id):
    """
    Obtém o histórico de jogos do usuário

    Args:
        user_id: ID do usuário

    Returns:
        dict: Histórico de sessões e estatísticas
    """
    try:
        db = DatabaseConnector()
        # Obter o usuário pelo ID
        user = db.get_user_by_id(user_id)

        if not user:
            return {"error": "Usuário não encontrado"}

        # Extrair histórico do usuário ou criar estrutura vazia
        history = user.get("history", {})
        if not history:
            history = {"completed_sessions": [], "statistics": {}}

        # Buscar sessões completadas do usuário
        sessions = history.get("completed_sessions", [])

        # Calcular estatísticas
        total_sessions = len(sessions)
        total_exercises = sum(session.get("exercises_completed", 0)
                              for session in sessions)

        # Calcular pontuação média
        if total_sessions > 0:
            average_score = sum(session.get("score", 0)
                                for session in sessions) / total_sessions
        else:
            average_score = 0

        # Contar sessões por dificuldade
        sessions_by_difficulty = {
            "iniciante": 0,
            "médio": 0,
            "avançado": 0
        }

        for session in sessions:
            difficulty = session.get("difficulty", "iniciante").lower()
            if difficulty in sessions_by_difficulty:
                sessions_by_difficulty[difficulty] += 1

        # Estruturar as estatísticas
        statistics = {
            "total_sessions": total_sessions,
            "total_exercises_completed": total_exercises,
            "average_score": round(average_score, 1),
            "sessions_by_difficulty": sessions_by_difficulty
        }

        # Buscar jogos completos na coleção de jogos
        completed_games = []
        if db.connected:
            cursor = db.db.games.find({
                "user_id": user_id,
                "completed": True
            }).sort("completed_at", -1)
            completed_games = list(cursor)

        # Estruturar resposta final
        response = {
            "sessions": sessions,
            "statistics": statistics,
            "completed_games": [
                {
                    "game_id": str(game.get("_id")),
                    "title": game.get("title", "Sem título"),
                    "completed_at": game.get("completed_at"),
                    "score": game.get("final_score", 0)
                } for game in completed_games
            ]
        }

        return response

    except Exception as e:
        print(f"❌ Erro ao obter histórico do usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def get_user_statistics(user_id):
    """
    Obtém estatísticas detalhadas do usuário

    Args:
        user_id: ID do usuário

    Returns:
        dict: Estatísticas do usuário
    """
    try:
        db = DatabaseConnector()
        # Obter o usuário pelo ID
        user = db.get_user_by_id(user_id)

        if not user:
            return {"error": "Usuário não encontrado"}

        # Obter estatísticas salvas ou criar novas
        stats = user.get("statistics", {})

        # Obter histórico
        history = user.get("history", {})
        sessions = history.get("completed_sessions", [])

        # Calcular estatísticas adicionais
        total_exercises_completed = stats.get("exercises_completed", 0)
        accuracy = stats.get("accuracy", 0)

        # Calcular tempo desde registro (em dias)
        from datetime import datetime
        created_at = user.get("created_at", datetime.now())
        days_since_registration = (datetime.now() - created_at).days

        # Determinar nível do usuário baseado nas estatísticas
        level = "iniciante"
        if total_exercises_completed > 50 and accuracy > 85:
            level = "avançado"
        elif total_exercises_completed > 20 and accuracy > 70:
            level = "médio"

        # Calcular progresso para o próximo nível
        level_progress = 0
        next_level = "médio"

        if level == "iniciante":
            # Progresso para médio (baseado em exercícios e precisão)
            ex_progress = min(100, (total_exercises_completed / 20) * 100)
            acc_progress = min(100, (accuracy / 70) * 100)
            level_progress = (ex_progress + acc_progress) / 2
            next_level = "médio"
        elif level == "médio":
            # Progresso para avançado
            ex_progress = min(100, (total_exercises_completed / 50) * 100)
            acc_progress = min(100, (accuracy / 85) * 100)
            level_progress = (ex_progress + acc_progress) / 2
            next_level = "avançado"
        else:
            # Avançado é o nível máximo, 100% de progresso
            level_progress = 100
            next_level = "avançado+"

        # Mensagem motivacional baseada no progresso
        if level_progress < 30:
            message = "Continue praticando para avançar!"
        elif level_progress < 70:
            message = f"Você está indo bem no caminho para {next_level}!"
        else:
            message = f"Quase lá! Você está muito próximo de alcançar o nível {next_level}!"

        # Criar distribuição por dificuldade
        difficulty_counts = {"iniciante": 0, "médio": 0, "avançado": 0}
        for session in sessions:
            difficulty = session.get("difficulty", "iniciante").lower()
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1

        # Calcular progresso semanal (últimos 7 dias)
        weekly_progress = []
        today = datetime.now().date()

        for i in range(6, -1, -1):
            day_offset = (today - datetime.timedelta(days=i))
            day_name = ["Segunda", "Terça", "Quarta", "Quinta",
                        "Sexta", "Sábado", "Domingo"][day_offset.weekday()]

            # Filtrar sessões deste dia
            day_sessions = [s for s in sessions if
                            datetime.fromisoformat(s.get("completed_at", "")).date() == day_offset]

            # Calcular média do dia
            day_avg = sum(s.get("score", 0)
                          for s in day_sessions) / max(1, len(day_sessions))

            weekly_progress.append({
                "day": day_name,
                "count": len(day_sessions),
                "avg_score": round(day_avg, 1)
            })

        # Tempo total gasto (estimado - 5 minutos por exercício)
        total_time_mins = total_exercises_completed * 5

        # Criar objeto de estatísticas completo
        statistics = {
            "exercises_completed": total_exercises_completed,
            "accuracy": accuracy,
            "current_level": level,
            "next_level": next_level,
            "level_progress_percentage": round(level_progress, 1),
            "level_progress_message": message,
            "joined_days_ago": days_since_registration,
            "total_sessions": len(sessions),
            "average_score": round(sum(s.get("score", 0) for s in sessions) / max(1, len(sessions)), 1),
            "difficulty_distribution": difficulty_counts,
            "weekly_progress": weekly_progress,
            "total_time_spent_mins": total_time_mins,
            "achievements_count": len(user.get("achievements", {}).get("earned", [])) if "achievements" in user else 0,
            "last_login": stats.get("last_login", ""),
            "last_activity": stats.get("last_activity", "")
        }

        return statistics

    except Exception as e:
        print(f"❌ Erro ao obter estatísticas do usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def get_user_achievements(user_id):
    """
    Obtém as conquistas do usuário

    Args:
        user_id: ID do usuário

    Returns:
        dict: Conquistas do usuário
    """
    try:
        db = DatabaseConnector()
        user = db.get_user_by_id(user_id)

        if not user:
            return {"error": "Usuário não encontrado"}

        # Verificar se o usuário tem conquistas salvas
        achievements = user.get("achievements", {})

        if not achievements:
            # Criar estrutura padrão de conquistas
            achievements = {
                "earned_achievements": [],
                "in_progress_achievements": [],
                "total_achievements": 10  # Número total de conquistas disponíveis no sistema
            }

            # Verificar conquistas automáticas baseadas em estatísticas
            stats = user.get("statistics", {})
            history = user.get("history", {})
            sessions = history.get("completed_sessions", [])

            # Lista de conquistas disponíveis
            all_achievements = [
                {
                    "id": "first_game",
                    "title": "Primeiro Passo",
                    "description": "Complete seu primeiro jogo",
                    "icon": "🎮",
                    "condition": lambda u: len(sessions) >= 1,
                    "progress": lambda u: min(1, len(sessions)),
                    "total": 1
                },
                {
                    "id": "practice_10",
                    "title": "Praticante Regular",
                    "description": "Complete 10 exercícios",
                    "icon": "🏅",
                    "condition": lambda u: stats.get("exercises_completed", 0) >= 10,
                    "progress": lambda u: stats.get("exercises_completed", 0),
                    "total": 10
                },
                {
                    "id": "practice_50",
                    "title": "Mestre da Prática",
                    "description": "Complete 50 exercícios",
                    "icon": "🏆",
                    "condition": lambda u: stats.get("exercises_completed", 0) >= 50,
                    "progress": lambda u: stats.get("exercises_completed", 0),
                    "total": 50
                },
                {
                    "id": "accuracy_master",
                    "title": "Precisão Perfeita",
                    "description": "Atinja uma precisão média de 90%",
                    "icon": "🎯",
                    "condition": lambda u: stats.get("accuracy", 0) >= 90,
                    "progress": lambda u: stats.get("accuracy", 0),
                    "total": 90
                },
                {
                    "id": "beginner_master",
                    "title": "Mestre Iniciante",
                    "description": "Complete 5 jogos no nível iniciante com pontuação acima de 80%",
                    "icon": "🥉",
                    "condition": lambda u: len([s for s in sessions
                                               if s.get("difficulty") == "iniciante" and s.get("score", 0) > 80]) >= 5,
                    "progress": lambda u: len([s for s in sessions
                                              if s.get("difficulty") == "iniciante" and s.get("score", 0) > 80]),
                    "total": 5
                },
                {
                    "id": "intermediate_master",
                    "title": "Mestre Intermediário",
                    "description": "Complete 5 jogos no nível médio com pontuação acima de 80%",
                    "icon": "🥈",
                    "condition": lambda u: len([s for s in sessions
                                               if s.get("difficulty") == "médio" and s.get("score", 0) > 80]) >= 5,
                    "progress": lambda u: len([s for s in sessions
                                              if s.get("difficulty") == "médio" and s.get("score", 0) > 80]),
                    "total": 5
                },
                {
                    "id": "advanced_master",
                    "title": "Mestre Avançado",
                    "description": "Complete 3 jogos no nível avançado com pontuação acima de 90%",
                    "icon": "🥇",
                    "condition": lambda u: len([s for s in sessions
                                               if s.get("difficulty") == "avançado" and s.get("score", 0) > 90]) >= 3,
                    "progress": lambda u: len([s for s in sessions
                                              if s.get("difficulty") == "avançado" and s.get("score", 0) > 90]),
                    "total": 3
                },
                {
                    "id": "daily_streak_7",
                    "title": "Semana Consistente",
                    "description": "Pratique por 7 dias consecutivos",
                    "icon": "📅",
                    "condition": lambda u: stats.get("consecutive_days", 0) >= 7,
                    "progress": lambda u: stats.get("consecutive_days", 0),
                    "total": 7
                },
                {
                    "id": "perfect_score",
                    "title": "Pontuação Perfeita",
                    "description": "Obtenha 100% em qualquer jogo",
                    "icon": "🌟",
                    "condition": lambda u: any(s.get("score", 0) == 100 for s in sessions),
                    "progress": lambda u: 1 if any(s.get("score", 0) == 100 for s in sessions) else 0,
                    "total": 1
                },
                {
                    "id": "explorer",
                    "title": "Explorador de Sons",
                    "description": "Jogue 5 jogos com diferentes focos de pronúncia",
                    "icon": "🔍",
                    "condition": lambda u: len(set(s.get("game_title", "") for s in sessions)) >= 5,
                    "progress": lambda u: len(set(s.get("game_title", "") for s in sessions)),
                    "total": 5
                }
            ]

            from datetime import datetime

            # Verificar quais conquistas foram alcançadas
            earned = []
            in_progress = []

            for achievement in all_achievements:
                try:
                    is_earned = achievement["condition"](user)
                    progress = achievement["progress"](user)
                    percentage = min(
                        100, int((progress / achievement["total"]) * 100))

                    if is_earned:
                        earned.append({
                            "id": achievement["id"],
                            "title": achievement["title"],
                            "description": achievement["description"],
                            "icon": achievement["icon"],
                            "earned_at": datetime.now().isoformat()
                        })
                    else:
                        in_progress.append({
                            "id": achievement["id"],
                            "title": achievement["title"],
                            "description": achievement["description"],
                            "icon": achievement["icon"],
                            "progress": progress,
                            "total": achievement["total"],
                            "percentage": percentage
                        })
                except Exception as e:
                    print(
                        f"Erro ao processar conquista {achievement['id']}: {str(e)}")

            # Salvar as conquistas processadas
            achievements = {
                "earned_achievements": earned,
                "in_progress_achievements": in_progress,
                "total_achievements": len(all_achievements)
            }

            # Salvar no usuário
            db.update_user(user_id, {"achievements": achievements})

        return achievements

    except Exception as e:
        print(f"❌ Erro ao obter conquistas do usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# Adicionar as funções de exportação
__all__ = [
    'DatabaseConnector',
    'get_user_history',
    'get_user_statistics',
    'get_user_achievements'
]

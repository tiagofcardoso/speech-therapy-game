from typing import Dict, Any, List
import logging
from utils.agent_logger import log_agent_call
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ProgressionManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PROGRESSION")
        self.logger.info("Progression Manager agent initialized")

    @log_agent_call
    async def initialize(self):
        """Initialize the progression manager agent"""
        self.logger.info("Initialization complete")
        return True

    @log_agent_call
    def determine_difficulty(self, user_profile: Dict[str, Any]) -> str:
        """Determine the appropriate difficulty level for a user"""
        self.logger.info(f"Determining difficulty for user profile")

        # Log analysis steps
        if "history" in user_profile and user_profile["history"]:
            sessions = user_profile["history"].get("completed_sessions", [])
            self.logger.info(f"Analyzing {len(sessions)} completed sessions")

        user_id = user_profile.get('id', 'unknown')
        self.logger.info(
            f"ProgressionManagerAgent.determine_difficulty called by MCP coordinator for user {user_id}")

        # Verificar corretamente o histórico do usuário
        history = user_profile.get('history', {})

        # Obter sessões completadas do dicionário history, que pode estar em diferentes formatos
        completed_sessions = []

        # Formato 1: history é um dicionário com uma chave 'completed_sessions'
        if isinstance(history, dict) and 'completed_sessions' in history:
            completed_sessions = history.get('completed_sessions', [])

        # Formato 2: history é uma lista direta de sessões
        elif isinstance(history, list):
            completed_sessions = history

        # Se temos sessões completadas, usar as últimas 3 para calcular a dificuldade
        if completed_sessions and len(completed_sessions) > 0:
            try:
                # Pegar até as últimas 3 sessões
                recent_sessions = completed_sessions[-3:] if len(
                    completed_sessions) >= 3 else completed_sessions

                # Calcular média de pontuação
                total_score = 0
                valid_sessions = 0

                for session in recent_sessions:
                    if isinstance(session, dict) and 'score' in session:
                        total_score += session.get('score', 0)
                        valid_sessions += 1

                # Evitar divisão por zero
                if valid_sessions > 0:
                    avg_score = total_score / valid_sessions
                    self.logger.info(
                        f"User {user_id} average score: {avg_score} from {valid_sessions} recent sessions")

                    if avg_score < 60:
                        difficulty = "iniciante"
                    elif avg_score < 85:
                        difficulty = "médio"
                    else:
                        difficulty = "avançado"

                    self.logger.info(
                        f"Difficulty determination complete: {difficulty}")
                    return difficulty
            except Exception as e:
                self.logger.error(f"Error processing user history: {str(e)}")
                # Continuar com a determinação baseada na idade em caso de erro

        # Se não temos histórico ou houve erro, usar a idade como base
        age = user_profile.get('age', 7)
        self.logger.info(
            f"Using age-based difficulty for user {user_id} with age {age}")

        if age < 6:
            difficulty = "iniciante"
        elif age < 9:
            difficulty = "médio"
        else:
            difficulty = "avançado"

        self.logger.info(f"Difficulty determination complete: {difficulty}")
        return difficulty

    def update_user_progress(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """
        Atualiza o progresso do usuário com base nos dados da sessão

        Args:
            user_id: ID do usuário
            session_data: Dados da sessão completada
        """
        if user_id not in self.user_history:
            self.user_history[user_id] = []

        # Adicionar dados relevantes da sessão ao histórico
        session_summary = {
            "completed_at": session_data.get("end_time"),
            "score": session_data.get("final_score", 0),
            "difficulty": session_data.get("difficulty", "iniciante"),
            "exercises_completed": len(session_data.get("responses", [])),
            "game_type": session_data.get("game_type", "exercícios de pronúncia")
        }

        self.user_history[user_id].append(session_summary)
        self.logger.info(f"Updated progress for user {user_id}")

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas do usuário com base no histórico

        Args:
            user_id: ID do usuário

        Returns:
            Estatísticas do usuário
        """
        if user_id not in self.user_history or not self.user_history[user_id]:
            return {
                "sessions_completed": 0,
                "avg_score": 0,
                "recommended_difficulty": "iniciante",
                "strengths": [],
                "areas_to_improve": []
            }

        sessions = self.user_history[user_id]
        avg_score = sum(session.get("score", 0)
                        for session in sessions) / len(sessions)

        return {
            "sessions_completed": len(sessions),
            "avg_score": avg_score,
            "recommended_difficulty": self._calculate_recommended_difficulty(avg_score),
            "strengths": self._identify_strengths(sessions),
            "areas_to_improve": self._identify_improvement_areas(sessions)
        }

    def _calculate_recommended_difficulty(self, avg_score: float) -> str:
        """Calcula a dificuldade recomendada com base na pontuação média"""
        if avg_score < 60:
            return "iniciante"
        elif avg_score < 85:
            return "médio"
        return "avançado"

    def _identify_strengths(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Identifica pontos fortes com base nas sessões do usuário"""
        # Este é um método simples que poderia ser expandido com mais lógica
        strengths = []

        # Verificar se o usuário tem bons resultados em sessões avançadas
        advanced_sessions = [s for s in sessions if s.get(
            "difficulty") == "avançado"]
        if advanced_sessions and sum(s.get("score", 0) for s in advanced_sessions) / len(advanced_sessions) >= 80:
            strengths.append("Excelente em exercícios avançados")

        # Outros pontos fortes poderiam ser identificados aqui

        return strengths

    def _identify_improvement_areas(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Identifica áreas de melhoria com base nas sessões do usuário"""
        # Este é um método simples que poderia ser expandido com mais lógica
        areas = []

        # Verificar se o usuário tem dificuldades em sessões básicas
        basic_sessions = [s for s in sessions if s.get(
            "difficulty") == "iniciante"]
        if basic_sessions and sum(s.get("score", 0) for s in basic_sessions) / len(basic_sessions) < 70:
            areas.append("Precisa melhorar em exercícios básicos")

        # Outras áreas de melhoria poderiam ser identificadas aqui

        return areas

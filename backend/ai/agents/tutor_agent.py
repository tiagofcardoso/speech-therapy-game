from typing import Dict, Any, Optional
import json
import logging
import os
from openai import OpenAI

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class TutorAgent:
    def __init__(self, game_designer: 'GameDesignerAgent'):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.logger = logging.getLogger("TutorAgent")
        self.game_designer = game_designer
        self.user_sessions = {}
        self.logger.info("TutorAgent initialized")

    def create_instructions(self, user_profile: Dict[str, Any], difficulty: str) -> Dict[str, str]:
        name = user_profile.get("name", "amigo")
        age = user_profile.get("age", 7)
        try:
            prompt = f"Crie instruções em português para {name}, {age} anos, nível {difficulty}. Retorne JSON com 'greeting', 'explanation', 'encouragement'."
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um terapeuta da fala amigável."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"Error creating instructions: {str(e)}")
            return {
                "greeting": f"Olá, {name}!",
                "explanation": "Vamos praticar palavras legais hoje!",
                "encouragement": "Você vai arrasar!"
            }

    def provide_feedback(self, user_id: str, response: str) -> Dict[str, Any]:
        current_exercise = self.game_designer.get_current_exercise(user_id)
        if not current_exercise:
            self.logger.warning(f"No active game for user {user_id}")
            return {"error": "Nenhum jogo ativo encontrado para este usuário"}

        game_type = self.game_designer.current_games[user_id]["game_type"]
        expected = self._get_expected_word(current_exercise, game_type)

        evaluation = self._evaluate_pronunciation(response, expected)
        score = evaluation.get("score", 5)
        explanation = evaluation.get("explanation", "Avaliação padrão")

        feedback = self._generate_feedback(score, explanation, expected)
        self._update_user_progress(user_id, score)

        return {
            "score": score,
            "message": feedback,
            "correct": score >= 7,
            "next_exercise": self.game_designer.get_current_exercise(user_id) is not None
        }

    def _get_expected_word(self, exercise: Dict[str, Any], game_type: str) -> str:
        if game_type == "palavras cruzadas":
            return exercise.get("word", "sol")
        elif game_type == "adivinhações":
            return exercise.get("answer", "sol")
        elif game_type == "rimas":
            return exercise.get("starter", "sol")
        elif game_type == "exercícios de pronúncia":
            return exercise.get("word", "sol")
        elif game_type == "desafios de pronúncia":
            return exercise.get("sentence", "sol").split()[0]
        return "sol"

    def _evaluate_pronunciation(self, actual: str, expected: str) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um assistente de terapia da fala. Avalie a precisão da pronúncia."},
                    {"role": "user", "content": (
                        f"Palavra esperada: '{expected}'. Pronúncia do usuário: '{actual}'. "
                        "Retorne um JSON com 'score' (1-10) e 'explanation' (string explicando o score)."
                    )}
                ],
                response_format={"type": "json_object"}
            )
            evaluation = json.loads(response.choices[0].message.content)
            self.logger.info(
                f"Pronunciation evaluation for {expected}: {evaluation}")
            return evaluation
        except Exception as e:
            self.logger.error(f"Error evaluating pronunciation: {str(e)}")
            return {"score": 5, "explanation": "Não foi possível avaliar a pronúncia"}

    def _generate_feedback(self, score: int, explanation: str, expected: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um terapeuta da fala amigável. Forneça feedback encorajador."},
                    {"role": "user", "content": (
                        f"Dê feedback encorajador para alguém que tentou dizer '{expected}'. "
                        f"Avaliação: score={score}, explicação={explanation}"
                    )}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating feedback: {str(e)}")
            return f"Ótima tentativa com '{expected}'! Vamos praticar mais."

    def _update_user_progress(self, user_id: str, score: int):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"attempts": 0, "total_score": 0}
        self.user_sessions[user_id]["attempts"] += 1
        self.user_sessions[user_id]["total_score"] += score
        self.game_designer.update_progress(user_id, score)
        self.logger.info(
            f"Updated progress for {user_id}: attempts={self.user_sessions[user_id]['attempts']}, total_score={self.user_sessions[user_id]['total_score']}")

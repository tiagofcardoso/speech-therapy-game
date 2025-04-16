from typing import Dict, Any, Optional
import uuid
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
import json
import sys
from pathlib import Path

# Add project root to Python path
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    # Navigate up to speech-therapy-game
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))

from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.progression_manager_agent import ProgressionManagerAgent
from ai.agents.tutor_agent import TutorAgent
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MCPCoordinator:
    def __init__(self, api_key: Optional[str] = None, db_connector=None):
        self.logger = logging.getLogger('MCPCoordinator')
        load_dotenv()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required.")

        self.client = OpenAI(api_key=self.api_key)
        self.sessions = {}
        self.db_connector = db_connector  # Salvar o db_connector

        self.game_designer = GameDesignerAgent()
        self.progression_manager = ProgressionManagerAgent()
        self.tutor = TutorAgent(self.game_designer)
        self.speech_evaluator = SpeechEvaluatorAgent()

        self.agents = {
            "game_designer": self.game_designer,
            "progression_manager": self.progression_manager,
            "tutor": self.tutor,
            "speech_evaluator": self.speech_evaluator
        }

        self.logger.info("MCPCoordinator initialized successfully")

    def connect(self) -> bool:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            if response.choices:
                self.logger.info("Successfully connected to OpenAI API")
                return True
            self.logger.error("Invalid response from OpenAI API")
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenAI API: {str(e)}")
            return False

    def disconnect(self) -> bool:
        self.logger.info("Disconnected from OpenAI API")
        return True

    def create_game_session(self, user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        try:
            difficulty = self.agents["progression_manager"].determine_difficulty(
                user_profile)
            game = self.agents["game_designer"].create_game(
                user_id, difficulty, db_connector=self.db_connector)  # Passando o db_connector para uso no histórico
            instructions = self.agents["tutor"].create_instructions(
                user_profile, difficulty)

            session = {
                "session_id": str(uuid.uuid4()),
                "user_id": user_id,
                "difficulty": difficulty,
                "game_type": game["game_type"],
                "exercises": game["content"],
                "instructions": instructions,
                "current_index": 0,
                "responses": [],
                "completed": False,
                "start_time": datetime.datetime.now().isoformat(),
                "end_time": None
            }

            self.sessions[user_id] = session
            self.logger.info(
                f"Game session created for user {user_id}: {session['session_id']}")
            return session
        except Exception as e:
            self.logger.error(f"Error creating game session: {str(e)}")
            return {"error": "Failed to create game session"}

    def process_response(self, session: Dict[str, Any], recognized_text: str) -> Dict[str, Any]:
        try:
            # Verificar se o texto foi reconhecido
            if not recognized_text or recognized_text == "Texto não reconhecido":
                # Gerar feedback para texto não reconhecido
                no_recognition_feedback = {
                    "praise": "Não consegui entender o que disseste. Por favor, tenta novamente falando mais claramente.",
                    "correction": "Fala um pouco mais alto e claro.",
                    "tip": "Tenta posicionar o microfone mais perto da boca.",
                    "encouragement": "Tu consegues!"
                }

                # Sintetizar áudio para o feedback, se necessário
                if self.tutor.voice_enabled:
                    try:
                        from backend.speech.synthesis import synthesize_speech
                        no_recognition_feedback["audio"] = synthesize_speech(
                            no_recognition_feedback["praise"])
                    except Exception as e:
                        self.logger.error(
                            f"Erro ao sintetizar feedback para texto não reconhecido: {str(e)}")

                return {
                    "session_complete": False,
                    "feedback": no_recognition_feedback,
                    "current_exercise": session.get("current_exercise"),
                    "repeat_exercise": True,
                    "recognition_failed": True
                }

            user_id = session["user_id"]
            current_index = session.get("current_index", 0)
            exercises = session.get("exercises", [])

            if current_index >= len(exercises):
                session["completed"] = True
                session["end_time"] = datetime.datetime.now().isoformat()
                self.logger.info(f"Session completed for user {user_id}")
                return {
                    "session_complete": True,
                    "feedback": {
                        "praise": "Ótimo trabalho ao completar todos os exercícios!",
                        "correction": None,
                        "tip": None,
                        "encouragement": "Você terminou a sessão!"
                    }
                }

            # Obter o exercício atual
            current_exercise = exercises[current_index]
            expected_text = current_exercise.get("target_text", "")

            # Usar o SpeechEvaluatorAgent para avaliar a pronúncia
            speech_evaluation = self.agents["speech_evaluator"].evaluate_speech(
                recognized_text, expected_text, session.get(
                    "difficulty", "medium")
            )

            # Obter feedback do TutorAgent baseado na avaliação
            feedback = self.agents["tutor"].provide_feedback(
                user_id, recognized_text, speech_evaluation=speech_evaluation
            )

            # Threshold de precisão
            is_correct = speech_evaluation["accuracy"] >= 0.7
            score = speech_evaluation["score"]

            if is_correct:
                session["current_index"] += 1
                session["responses"].append({
                    "exercise_index": current_index,
                    "recognized_text": recognized_text,
                    "expected_text": expected_text,
                    "is_correct": is_correct,
                    "accuracy": speech_evaluation["accuracy"],
                    "score": score,
                    "details": speech_evaluation.get("details", {})
                })

                # Atualizar o progresso no GameDesigner, passando o db_connector
                self.game_designer.update_progress(
                    user_id, score, self.db_connector)

            # Salvar a sessão atualizada no banco de dados
            if self.db_connector:
                self.db_connector.save_session(session)

            session_complete = session["current_index"] >= len(exercises)
            if session_complete:
                session["completed"] = True
                session["end_time"] = datetime.datetime.now().isoformat()

            next_exercise = None
            if not session_complete:
                next_index = session["current_index"]
                next_exercise = {
                    **exercises[next_index], "index": next_index, "total": len(exercises)}

            self.sessions[user_id] = session

            # Gerar feedback personalizado baseado na avaliação de fala
            correction_tip = None
            if not is_correct and "improvement_areas" in speech_evaluation:
                correction_tip = speech_evaluation["improvement_areas"][0] if speech_evaluation[
                    "improvement_areas"] else "Tenta pronunciar mais claramente"

            self.logger.info(
                f"Processed response for user {user_id}: correct={is_correct}, accuracy={speech_evaluation['accuracy']:.2f}")

            return {
                "session_complete": session_complete,
                "feedback": {
                    "praise": feedback["message"],
                    "correction": None if is_correct else f"Tenta dizer '{expected_text}' novamente",
                    "tip": correction_tip if not is_correct else "Excelente pronúncia!",
                    "encouragement": feedback.get("encouragement", "Continua assim!"),
                    "accuracy": speech_evaluation["accuracy"]
                },
                "current_exercise": next_exercise,
                "repeat_exercise": not is_correct,
                "pronunciation_details": speech_evaluation.get("details", {})
            }
        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return {"error": "Failed to process response"}


if __name__ == "__main__":
    coordinator = MCPCoordinator()
    user_profile = {"name": "João", "age": 7}
    session = coordinator.create_game_session("user123", user_profile)
    print(json.dumps(session, indent=2, ensure_ascii=False))

    response = coordinator.process_response(session, "sol")
    print(json.dumps(response, indent=2, ensure_ascii=False))

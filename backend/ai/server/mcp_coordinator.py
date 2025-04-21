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
import time
import tempfile
import subprocess
import traceback

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
from speech.recognition import recognize_speech
from speech.synthesis import synthesize_speech

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
        self.speech_evaluator = SpeechEvaluatorAgent(self.client)

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
                # Passando o db_connector para uso no histórico
                user_id, difficulty, db_connector=self.db_connector)
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

    def evaluate_pronunciation(self, user_id, audio_file_storage, expected_word):
        """
        Avalia a pronúncia de uma palavra a partir de um arquivo de áudio.
        Encapsula a lógica de salvamento, conversão, reconhecimento e avaliação.
        """
        temp_path = None
        wav_path = None
        audio_path_for_recognition = None  # Inicializar
        try:
            # 1. Salvar arquivo de áudio temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm", prefix=f"pronunciation_{user_id}_") as temp_webm:
                audio_file_storage.save(temp_webm.name)
                temp_path = temp_webm.name
            self.logger.info(
                f"✓ Audio saved to temporary path: {temp_path}")  # Usar logger

            # 2. Converter WebM para WAV usando ffmpeg
            try:
                wav_path = temp_path.replace(".webm", ".wav")
                self.logger.info(
                    # Log antes
                    f"Attempting conversion: {temp_path} -> {wav_path}")
                result = subprocess.run([
                    'ffmpeg', '-y', '-i', temp_path,
                    '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', wav_path
                ], capture_output=True, text=True, check=True)
                # Log detalhado do ffmpeg
                self.logger.info(
                    f"✓ FFmpeg conversion successful. Output:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
                audio_path_for_recognition = wav_path

                # *** NOVO: Verificar se o arquivo WAV existe e tem tamanho > 0 ***
                if os.path.exists(audio_path_for_recognition):
                    file_size = os.path.getsize(audio_path_for_recognition)
                    self.logger.info(
                        f"✓ WAV file exists: {audio_path_for_recognition}, Size: {file_size} bytes")
                    if file_size == 0:
                        self.logger.warning(
                            f"⚠️ WAV file is empty! Path: {audio_path_for_recognition}")
                        # Considerar tratar como erro ou usar o original
                        # Fallback para o original se o WAV estiver vazio
                        audio_path_for_recognition = temp_path
                        self.logger.info(
                            f"Falling back to original file: {audio_path_for_recognition}")
                else:
                    self.logger.error(
                        f"❌ WAV file does NOT exist after conversion! Path: {audio_path_for_recognition}")
                    audio_path_for_recognition = temp_path  # Fallback para o original
                    self.logger.info(
                        f"Falling back to original file: {audio_path_for_recognition}")

            except subprocess.CalledProcessError as e:
                self.logger.warning(
                    f"⚠️ FFmpeg conversion error (Code: {e.returncode}): {e.stderr}. Using original file.")
                audio_path_for_recognition = temp_path
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Audio conversion error: {str(e)}. Using original file.")
                audio_path_for_recognition = temp_path

            # Garantir que temos um caminho para tentar o reconhecimento
            if not audio_path_for_recognition:
                self.logger.error(
                    "❌ No valid audio path available for recognition after save/convert attempts.")
                raise ValueError(
                    "Failed to prepare audio file for recognition")

            # 3. Tentar reconhecimento de fala
            recognized_text = None  # Inicializar
            self.logger.info(
                f"Attempting speech recognition on: {audio_path_for_recognition}")
            try:
                # *** NOVO: Log extra antes da chamada ***
                self.logger.info(
                    f"Calling recognize_speech with path='{audio_path_for_recognition}', expected='{expected_word}'")
                recognized_text = recognize_speech(
                    audio_path_for_recognition, expected_word)
                # *** NOVO: Log do resultado bruto ***
                self.logger.info(
                    f"✓ Raw recognition result: '{recognized_text}'")

            except Exception as e:
                # *** NOVO: Capturar exceções específicas do reconhecimento ***
                self.logger.error(
                    f"❌ Exception during recognize_speech call: {str(e)}")
                # Log completo do stack trace
                self.logger.error(traceback.format_exc())
                recognized_text = None  # Garantir que é None em caso de exceção

            # 4. Lidar com falha no reconhecimento (incluindo exceções ou resultado vazio/padrão)
            # *** MODIFICADO: Checar explicitamente por None também ***
            if recognized_text is None or recognized_text.strip() == "" or recognized_text == "Text not recognized" or recognized_text == "Texto não reconhecido":
                self.logger.warning(
                    # Log aprimorado
                    f"⚠️ Speech recognition failed or returned empty/default. Result: '{recognized_text}'")
                feedback = "Não consegui entender o que você disse. Por favor, tente falar mais claramente."
                try:
                    audio_feedback = synthesize_speech(feedback)
                except Exception as synth_e:
                    self.logger.warning(
                        f"⚠️ Error generating audio feedback for unrecognized speech: {synth_e}")
                    audio_feedback = None
                return {
                    "success": True,
                    "isCorrect": False,
                    "score": 3,
                    "recognized_text": "",
                    "feedback": feedback,
                    "audio_feedback": audio_feedback
                }

            # 5. Avaliar a fala reconhecida usando o agente
            self.logger.info(
                f"Proceeding with evaluation for recognized text: '{recognized_text}'")
            try:
                evaluation = self.speech_evaluator.evaluate_speech(
                    spoken_text=recognized_text,
                    expected_text=expected_word,
                    difficulty="medium"
                )
            except Exception as e:
                self.logger.error(f"⚠️ Speech evaluation error: {str(e)}")
                evaluation = {
                    "accuracy": 0.5,
                    "details": {"phonetic_analysis": "Houve um problema na avaliação da pronúncia."},
                    "strengths": [],
                    "improvement_areas": []
                }

            # 6. Gerar feedback textual e de áudio
            accuracy_score = int(evaluation.get("accuracy", 0.5) * 10)
            is_correct = accuracy_score >= 7

            feedback_text = evaluation.get("details", {}).get(
                "phonetic_analysis",
                "Muito bem!" if is_correct else "Continue praticando, você consegue!"
            )

            try:
                audio_feedback = synthesize_speech(feedback_text)
            except Exception as e:
                self.logger.warning(f"⚠️ Error generating audio feedback: {e}")
                audio_feedback = None

            return {
                "success": True,
                "isCorrect": is_correct,
                "score": accuracy_score,
                "recognized_text": recognized_text,
                "matched_sounds": evaluation.get("strengths", []),
                "challenging_sounds": evaluation.get("improvement_areas", []),
                "feedback": feedback_text,
                "audio_feedback": audio_feedback
            }

        except Exception as e:
            self.logger.error(
                f"❌ Pronunciation evaluation error in Coordinator: {str(e)}")
            self.logger.error(traceback.format_exc())
            error_feedback_text = "Ocorreu um erro inesperado ao avaliar sua pronúncia."
            try:
                error_audio_feedback = synthesize_speech(error_feedback_text)
            except:
                error_audio_feedback = None
            return {
                "success": False,
                "message": f"Error during evaluation: {str(e)}",
                "error_code": "EVALUATION_FAILED_INTERNAL",
                "feedback": error_feedback_text,
                "audio_feedback": error_audio_feedback,
                "isCorrect": False,
                "score": 0,
                "recognized_text": "",
                "matched_sounds": [],
                "challenging_sounds": [],
            }
        finally:
            try:
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
                    self.logger.info(f"✓ Cleaned up WAV file: {wav_path}")
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                    self.logger.info(
                        f"✓ Cleaned up temporary file: {temp_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Error cleaning temp files: {e}")


if __name__ == "__main__":
    coordinator = MCPCoordinator()
    user_profile = {"name": "João", "age": 7}
    session = coordinator.create_game_session("user123", user_profile)
    print(json.dumps(session, indent=2, ensure_ascii=False))

    response = coordinator.process_response(session, "sol")
    print(json.dumps(response, indent=2, ensure_ascii=False))

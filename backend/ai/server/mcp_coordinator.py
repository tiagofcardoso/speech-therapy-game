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
from bson import ObjectId  # Certifique-se de importar ObjectId

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
                    format='%(asctime)s - %(name%s - %(levelname)s - %(message)s')


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

    def _prepare_exercises(self, raw_exercises):
        """Helper interno para processar e validar exercícios."""
        exercises = []
        if not raw_exercises:
            self.logger.warning("No raw exercises provided. Creating default.")
            return [{
                "word": "teste", "prompt": "Pronuncie esta palavra",
                "hint": "Fale devagar", "visual_cue": "teste"
            }]

        for idx, exercise in enumerate(raw_exercises):
            if not isinstance(exercise, dict):
                self.logger.warning(
                    f"Skipping non-dict exercise at index {idx}: {exercise}")
                continue

            word = exercise.get("word",
                                exercise.get("text",
                                             exercise.get("answer",
                                                          exercise.get("target_word",  # <-- Exemplo: Adicione a chave encontrada no DB aqui
                                                                       # <-- Ou outra chave possível
                                                                       exercise.get("stimulus", "")))))
            if not word:
                word = f"palavra{idx+1}"
                self.logger.warning(
                    f"Empty word detected in exercise {idx}, using '{word}' as fallback")

            transformed_exercise = {
                "word": word,
                "prompt": exercise.get("prompt", exercise.get("tip", "Pronuncie esta palavra")),
                "hint": exercise.get("hint", exercise.get("tip", "Fale devagar")),
                # Usar a palavra como fallback para visual_cue
                "visual_cue": exercise.get("visual_cue", word)
            }
            exercises.append(transformed_exercise)

        if not exercises:  # Se todos falharam, retornar padrão
            self.logger.warning(
                "Failed to process any exercise. Creating default.")
            return [{
                "word": "teste", "prompt": "Pronuncie esta palavra",
                "hint": "Fale devagar", "visual_cue": "teste"
            }]
        return exercises

    def load_existing_game_session(self, user_id: str, game_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Carrega um jogo existente e cria uma nova sessão para ele."""
        self.logger.info(f"Loading existing game {game_id} for user {user_id}")
        try:
            game_data = self.db_connector.get_game(game_id)
            if not game_data:
                self.logger.error(f"Game {game_id} not found in DB.")
                raise ValueError(f"Jogo com ID {game_id} não encontrado.")

            self.logger.info(
                f"Game found: {game_data.get('title', 'Sem título')}")

            # Extrair exercícios do jogo
            content = game_data.get("content", {})
            raw_exercises = []
            if isinstance(content, dict) and "exercises" in content:
                raw_exercises = content.get("exercises", [])
            elif isinstance(content, dict) and "content" in content:
                raw_exercises = content.get("content", [])
            elif "exercises" in game_data:
                raw_exercises = game_data.get("exercises", [])
            elif "content" in game_data and isinstance(game_data.get("content"), list):
                raw_exercises = game_data.get("content", [])
            elif isinstance(content, list):
                raw_exercises = content

            exercises = self._prepare_exercises(raw_exercises)

            # Criar dados da sessão
            session_data = {
                "session_id": str(uuid.uuid4()),
                "user_id": user_id,
                "game_id": game_id,
                "game_title": game_data.get("title", "Jogo Carregado"),
                "difficulty": game_data.get("difficulty", "iniciante"),
                "game_type": game_data.get("game_type", "exercícios"),
                "exercises": exercises,
                "instructions": game_data.get("instructions", ["Bem-vindo de volta!"]),
                "current_index": 0,
                "responses": [],
                "completed": False,
                "start_time": datetime.datetime.now().isoformat(),
                "end_time": None,
                "created_at": datetime.datetime.now().isoformat()  # Adicionar created_at
            }

            # Salvar a nova sessão no DB
            session_id_saved = self.db_connector.save_session(session_data)
            self.logger.info(
                f"New session created ({session_id_saved}) for existing game {game_id}")

            # Retornar dados necessários para a resposta da API
            return {
                "success": True,
                "session_id": session_data["session_id"],
                "instructions": session_data["instructions"],
                # Retornar todos para o frontend calcular total
                "exercises": session_data["exercises"]
            }

        except Exception as e:
            self.logger.error(
                f"Error loading game session for game {game_id}: {e}")
            self.logger.error(traceback.format_exc())
            return {"success": False, "message": f"Erro ao carregar sessão do jogo: {e}"}

    def create_new_game_session(self, user_id: str, user_profile: Dict[str, Any], difficulty: str, title: str, game_type: str) -> Dict[str, Any]:
        """Cria uma nova sessão de jogo, potencialmente gerando conteúdo."""
        self.logger.info(
            f"Creating new game session for user {user_id}. Difficulty: {difficulty}")
        try:
            # TODO: Adicionar lógica para gerar exercícios aqui se necessário,
            # por enquanto, vamos usar um placeholder simples.
            # Poderia chamar self.game_designer.create_game(...) aqui se quisesse gerar
            # um jogo dinâmico que não precisa ser pré-salvo.

            placeholder_exercises = self._prepare_exercises([
                {"word": "exemplo", "prompt": "Diga 'exemplo'",
                    "hint": "Começa com 'e'"},
                {"word": "novo", "prompt": "Diga 'novo'", "hint": "Termina com 'o'"}
            ])

            session_data = {
                "session_id": str(uuid.uuid4()),
                "user_id": user_id,
                "game_id": None,  # Nenhum jogo pré-existente
                "game_title": title,
                "difficulty": difficulty,
                "game_type": game_type,
                "exercises": placeholder_exercises,
                "instructions": [f"Olá {user_profile.get('name', 'jogador')}! Bem-vindo a um novo desafio de {game_type}!"],
                "current_index": 0,
                "responses": [],
                "completed": False,
                "start_time": datetime.datetime.now().isoformat(),
                "end_time": None,
                "created_at": datetime.datetime.now().isoformat()  # Adicionar created_at
            }

            # Salvar a nova sessão no DB
            session_id_saved = self.db_connector.save_session(session_data)
            self.logger.info(
                f"New session created and saved: {session_id_saved}")

            # Retornar dados necessários para a resposta da API
            return {
                "success": True,
                "session_id": session_data["session_id"],
                "instructions": session_data["instructions"],
                # Retornar todos para o frontend calcular total
                "exercises": session_data["exercises"]
            }

        except Exception as e:
            self.logger.error(
                f"Error creating new game session for user {user_id}: {e}")
            self.logger.error(traceback.format_exc())
            return {"success": False, "message": f"Erro ao criar nova sessão: {e}"}

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

    def finalize_session(self, session_id: str, user_id: str, final_score: float, completion_option: str, completed_manually: bool = False, generate_next: bool = False) -> Dict[str, Any]:
        """
        Finaliza uma sessão de jogo, atualiza o DB, estatísticas do usuário e opcionalmente gera o próximo jogo.
        """
        self.logger.info(
            f"Attempting to finalize session {session_id} for user {user_id}")
        response_data = {"success": False,
                         "message": "Erro desconhecido ao finalizar"}
        try:
            # 1. Buscar sessão
            session = self.db_connector.get_session(session_id)
            if not session:
                self.logger.error(f"Session not found: {session_id}")
                return {"success": False, "message": "Sessão não encontrada"}
            if str(session.get('user_id')) != str(user_id):
                self.logger.warning(
                    f"User mismatch: {user_id} tried to finish session {session_id} owned by {session.get('user_id')}")
                return {"success": False, "message": "Permissão negada"}

            # 2. Atualizar dados da sessão
            exercises_completed_count = len(session.get(
                'exercises', []))  # Calcular antes de atualizar
            update_data = {
                'completed': True,
                'end_time': datetime.datetime.now().isoformat(),
                'completed_manually': completed_manually,
                'completion_option': completion_option,
                'final_score': final_score,
                'exercises_completed': exercises_completed_count
            }
            session_update_success = self.db_connector.update_session(
                session_id, update_data)
            if not session_update_success:
                self.logger.error(
                    f"Failed to update session {session_id} in DB.")
                # Considerar retornar erro aqui se a atualização da sessão for crítica

            # 3. Atualizar jogo (se aplicável)
            game_id = session.get('game_id')
            if game_id:
                game_update_data = {
                    'completed': True,
                    'completed_at': datetime.datetime.now().isoformat(),
                    'final_score': final_score
                }
                game_update_success = self.db_connector.update_game(
                    game_id, game_update_data)
                if not game_update_success:
                    self.logger.warning(
                        f"Failed to update game {game_id} status.")

            # 4. Atualizar estatísticas e histórico do usuário
            user = self.db_connector.get_user_by_id(user_id)
            if user:
                current_exercises = user.get(
                    'statistics', {}).get('exercises_completed', 0)
                current_accuracy = user.get(
                    'statistics', {}).get('accuracy', 0)
                # Contar sessões completas no histórico ANTES de adicionar a nova
                completed_sessions_count = len([s for s in user.get('history', {}).get(
                    'completed_sessions', []) if s.get('score') is not None])

                new_accuracy = ((current_accuracy * completed_sessions_count) + final_score) / (
                    completed_sessions_count + 1) if (completed_sessions_count + 1) > 0 else final_score

                user_updates = {
                    'statistics.exercises_completed': current_exercises + exercises_completed_count,
                    'statistics.last_activity': datetime.datetime.now().isoformat(),
                    'statistics.accuracy': round(new_accuracy, 2)
                }
                session_summary = {
                    'session_id': session_id,
                    'completed_at': datetime.datetime.now().isoformat(),
                    'difficulty': session.get('difficulty', 'iniciante'),
                    'score': final_score,
                    'exercises_completed': exercises_completed_count,
                    'game_id': game_id,
                    'game_title': session.get('game_title', 'Jogo sem título')
                }
                try:
                    self.db_connector.update_user(user_id, user_updates)
                    self.db_connector.add_to_user_history(
                        user_id, session_summary)
                    self.logger.info(
                        f"User statistics and history updated for {user_id}")
                except Exception as user_err:
                    self.logger.error(
                        f"Error updating user stats/history for {user_id}: {user_err}")

            # 5. Preparar resposta base
            response_data = {
                "success": True,
                "message": "Jogo finalizado com sucesso",
                "final_score": final_score
            }

            # 6. Gerar próximo jogo (se solicitado)
            if generate_next:
                try:
                    current_difficulty = session.get('difficulty', 'iniciante')
                    difficulty_map = {
                        'iniciante': 'médio' if final_score > 90 else 'iniciante',
                        'médio': 'avançado' if final_score > 90 else 'médio',
                        'avançado': 'avançado'
                    }
                    next_difficulty = difficulty_map.get(
                        current_difficulty, 'iniciante')

                    # Usar o agente GameDesigner que já existe no coordenador
                    next_game_data = self.game_designer.create_game(
                        user_id=user_id,
                        difficulty=next_difficulty,
                        game_type="exercícios de pronúncia"  # Ou obter do tipo de sessão atual
                    )

                    if next_game_data:
                        next_game_id = self.db_connector.store_game(
                            user_id, next_game_data)
                        response_data["next_game"] = {
                            "game_id": str(next_game_id),
                            "title": next_game_data.get("title", "Próximo Jogo"),
                            "difficulty": next_difficulty
                        }
                        self.logger.info(
                            f"Generated next game suggestion: {next_game_id}")
                except Exception as next_game_err:
                    self.logger.error(
                        f"Failed to generate next game: {next_game_err}")
                    # Não falhar a finalização se a geração do próximo falhar

            self.logger.info(f"Session {session_id} finalized successfully.")
            return response_data

        except Exception as e:
            self.logger.error(f"Error finalizing session {session_id}: {e}")
            self.logger.error(traceback.format_exc())
            return {"success": False, "message": f"Erro interno ao finalizar: {e}"}


if __name__ == "__main__":
    coordinator = MCPCoordinator()
    user_profile = {"name": "João", "age": 7}
    session = coordinator.create_game_session("user123", user_profile)
    print(json.dumps(session, indent=2, ensure_ascii=False))

    response = coordinator.process_response(session, "sol")
    print(json.dumps(response, indent=2, ensure_ascii=False))

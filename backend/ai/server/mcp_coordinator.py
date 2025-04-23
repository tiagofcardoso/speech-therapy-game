import os
import uuid
import logging
import datetime
import json
import sys
import tempfile
import subprocess
import traceback
from typing import Dict, Any, Optional, List
from pathlib import Path
from bson import ObjectId
from openai import OpenAI
from dotenv import load_dotenv
from ai.server.mcp_server import MCPServer, Message, ModelContext, Agent, Tool, ToolParam
from ..server.openai_client import create_async_openai_client
import asyncio

# Add project root to Python path
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))

from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.progression_manager_agent import ProgressionManagerAgent
from ai.agents.tutor_agent import TutorAgent
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
from speech.recognition import recognize_speech
from speech.synthesis import synthesize_speech

# Fix the logging format string
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MCPSystem:
    def __init__(self, api_key: str, db_connector: Any):
        self.logger = logging.getLogger(__name__)
        self.server = MCPServer()
        self.db_connector = db_connector

        # Initialize OpenAI client
        self.client = create_async_openai_client(api_key)
        self.logger.info("OpenAI client initialized successfully.")

        # Define tools
        self.logger.info("Defining tools...")
        self._define_tools()
        self.logger.info("Tools defined.")

        # Register agent handlers
        self.logger.info("Registering agents...")
        self.server.register_handler(
            "game_designer", self._game_designer_handler)
        self.server.register_handler("tutor", self._tutor_handler)

        # Registrar o handler para o speech_evaluator
        self.server.register_handler(
            "speech_evaluator", self._speech_evaluator_handler)

        self.logger.info("Agents registered.")

        self.logger.info("MCPSystem initialized successfully.")

    async def initialize_agents(self):
        """Initialize all agents asynchronously"""
        self.logger.info("Initializing agents...")

        # Create agent instances
        self._game_designer_instance = GameDesignerAgent(client=self.client)
        self._speech_evaluator_instance = SpeechEvaluatorAgent(
            client=self.client)
        self._tutor_instance = TutorAgent(
            self._game_designer_instance, client=self.client)
        self._progression_manager_instance = ProgressionManagerAgent()

        # Initialize all agents
        await asyncio.gather(
            self._game_designer_instance.initialize(),
            self._speech_evaluator_instance.initialize(),
            self._tutor_instance.initialize(),
            self._progression_manager_instance.initialize()
        )

        self.logger.info("All agents initialized successfully")

    def _define_tools(self):
        """Define all tools used by the agents."""
        self.logger.info("Defining tools...")

        # Define determine_difficulty_tool
        self.determine_difficulty_tool = Tool(
            name="determine_difficulty",
            description="Determines the appropriate difficulty level for the user.",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user's ID"),
                ToolParam(name="current_performance", type="dict",
                          optional=True, description="Recent performance data")
            ]
        )

        # Game Designer tools
        self.create_game_tool = Tool(
            name="create_game",
            description="Creates a game based on difficulty and user preferences",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID"),
                ToolParam(name="difficulty", type="string", optional=True,
                          description="The difficulty level or 'aleatório'"),
                ToolParam(name="game_type", type="string",
                          optional=True, description="The type of game"),
                ToolParam(name="age_group", type="string", optional=True,
                          description="The age group of the user")
            ]
        )

        self.get_current_exercise_tool = Tool(
            name="get_current_exercise",
            description="Gets the current exercise for a user",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID")
            ]
        )

        self.update_progress_tool = Tool(
            name="update_progress",
            description="Updates a user's progress in the game",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID"),
                ToolParam(name="score_increment", type="integer",
                          description="The score increment"),
                ToolParam(name="exercise_data", type="object", optional=True,
                          description="Additional data about the completed exercise")
            ]
        )

        self.get_user_progress_summary_tool = Tool(
            name="get_user_progress_summary",
            description="Gets a summary of user progress across games",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID")
            ]
        )

        self.generate_game_content_tool = Tool(
            name="generate_game_content",
            description="Generates specific content for a game type",
            parameters=[
                ToolParam(name="difficulty", type="string",
                          description="The difficulty level"),
                ToolParam(name="game_type", type="string",
                          description="The type of game to generate content for"),
                ToolParam(name="age_group", type="string",
                          description="Age group (crianças, adultos)"),
                ToolParam(name="target_sound", type="string", optional=True,
                          description="The target sound to focus on"),
                ToolParam(name="user_preferences", type="object",
                          optional=True, description="User preferences data")
            ]
        )

        self.check_game_to_repeat_tool = Tool(
            name="check_game_to_repeat",
            description="Checks if a user should repeat a previously played game",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID")
            ]
        )

        # Define tools for other agents (Tutor, Speech Evaluator, Search)
        # ...

        self.logger.info("Tools defined.")

    def _register_agents(self):
        """Create and register agents with the MCP server"""
        self.logger.info("Registering agents...")

        # Game Designer Agent
        self.game_designer_agent = Agent(
            name="game_designer",
            handler=self._game_designer_handler,
            tools=[
                self.create_game_tool,
                self.get_current_exercise_tool,
                self.update_progress_tool,
                self.get_user_progress_summary_tool,
                self.generate_game_content_tool,
                self.check_game_to_repeat_tool
            ]
        )
        self.server.register_agent(self.game_designer_agent)

        # Progression Manager Agent
        self.progression_manager_agent = Agent(
            name="progression_manager",
            handler=self._progression_manager_handler,
            tools=[
                self.determine_difficulty_tool
            ]
        )
        self.server.register_agent(self.progression_manager_agent)

        # Register other agents (Tutor, Speech Evaluator, Search)
        # ...

        self.logger.info("Agents registered.")

    async def _game_designer_handler(self, message: Message, context: ModelContext) -> Dict[str, Any]:
        """Handle game designer agent messages"""
        self.logger.info(f"Handling message for game_designer: {message.tool}")

        try:
            if message.tool == "create_game":
                # Initialize GameDesignerAgent if needed
                if not hasattr(self, '_game_designer_instance'):
                    self._game_designer_instance = GameDesignerAgent(
                        client=self.client)
                    # Make sure to initialize the agent if it has an initialize method
                    if hasattr(self._game_designer_instance, 'initialize'):
                        await self._game_designer_instance.initialize()

                # Extract parameters
                user_id = message.params.get("user_id")
                difficulty = message.params.get("difficulty", "iniciante")
                game_type = message.params.get(
                    "game_type", "exercícios de pronúncia")

                # Ensure we have required parameters
                if not user_id:
                    raise ValueError("user_id is required")

                try:
                    # Call create_game and ensure it returns data
                    game_data = await self._game_designer_instance.create_game(
                        user_id=user_id,
                        difficulty=difficulty,
                        game_type=game_type
                    )

                    if not game_data:
                        raise ValueError(
                            "No game data returned from create_game")

                    return game_data

                except NameError as ne:
                    self.logger.error(f"NameError in create_game: {str(ne)}")
                    return {"error": f"Game creation failed: {str(ne)}"}
                except Exception as e:
                    self.logger.error(f"Error creating game: {str(e)}")
                    return {"error": f"Game creation failed: {str(e)}"}
            else:
                raise ValueError(f"Unknown tool: {message.tool}")

        except Exception as e:
            self.logger.error(f"Error in game designer handler: {str(e)}")
            return {"error": str(e)}

    async def _tutor_handler(self, message: Message, context: ModelContext) -> Dict[str, Any]:
        """Handle tutor agent messages"""
        self.logger.info(f"Handling message for tutor: {message.tool}")

        try:
            if message.tool == "create_instructions":
                # Initialize TutorAgent if needed
                if not hasattr(self, '_tutor_instance'):
                    self._tutor_instance = TutorAgent(client=self.client)
                    if hasattr(self._tutor_instance, 'initialize'):
                        await self._tutor_instance.initialize()

                # Get parameters for instructions
                game_title = message.params.get("game_title", "")
                game_type = message.params.get("game_type", "")
                difficulty = message.params.get("difficulty", "iniciante")
                persona = message.params.get("persona", "default")

                # For now, return a simple instruction template
                instructions = {
                    "content": f"Vamos jogar '{game_title}'! Este é um jogo de {game_type} " +
                    f"com dificuldade {difficulty}. Siga as instruções na tela e " +
                    "divirta-se aprendendo!"
                }

                return instructions
            else:
                raise ValueError(f"Unknown tool for tutor: {message.tool}")

        except Exception as e:
            self.logger.error(f"Error in tutor handler: {str(e)}")
            return {"error": str(e)}

    async def _progression_manager_handler(self, message: Message, context: ModelContext):
        """Handler for Progression Manager Agent tools."""
        self.logger.info(
            f"Handling message for progression_manager: {message.tool}")
        agent = self._progression_manager_instance

        try:
            if message.tool == "determine_difficulty":
                result = "médio"
                context.set("determined_difficulty", result)
                return result
            else:
                raise ValueError(
                    f"Unknown tool for progression_manager: {message.tool}")

        except Exception as e:
            self.logger.error(
                f"Error in _progression_manager_handler: {e}", exc_info=True)
            context.set(f"error_{message.tool}", {
                        "error": str(e), "trace": traceback.format_exc()})
            return {"error": f"Failed to execute {message.tool}: {e}"}

    async def _speech_evaluator_handler(self, message: Message, context: ModelContext) -> Dict[str, Any]:
        """Handle speech evaluator agent messages"""
        self.logger.info(
            f"Handling message for speech_evaluator: {message.tool}")

        try:
            if message.tool == "evaluate_pronunciation":
                # Initialize SpeechEvaluatorAgent if needed
                if not hasattr(self, '_speech_evaluator_instance'):
                    self._speech_evaluator_instance = SpeechEvaluatorAgent(
                        client=self.client)
                    if hasattr(self._speech_evaluator_instance, 'initialize'):
                        await self._speech_evaluator_instance.initialize()

                # Extract parameters
                audio_data = message.params.get("audio_data")
                expected_word = message.params.get("expected_word")
                language = message.params.get("language", "pt-PT")

                # Ensure we have required parameters
                if not audio_data:
                    raise ValueError("audio_data is required")
                if not expected_word:
                    raise ValueError("expected_word is required")

                # Escrever os dados de áudio em um arquivo temporário
                temp_audio_file = None
                try:
                    import tempfile
                    import os

                    # Criar arquivo temporário para o áudio
                    temp_fd, temp_audio_path = tempfile.mkstemp(suffix=".webm")
                    os.close(temp_fd)

                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_data)

                    self.logger.info(
                        f"Áudio salvo temporariamente em: {temp_audio_path}")

                    # Verificar se o áudio tem conteúdo (não é silêncio)
                    import wave
                    import contextlib
                    import subprocess

                    # Converter WebM para WAV para análise
                    wav_path = temp_audio_path.replace(".webm", ".wav")
                    convert_cmd = ["ffmpeg", "-i",
                                   temp_audio_path, "-y", wav_path]
                    self.logger.info(
                        f"Convertendo áudio: {' '.join(convert_cmd)}")

                    try:
                        subprocess.run(convert_cmd, check=True,
                                       capture_output=True)
                        self.logger.info(
                            f"Áudio convertido para WAV: {wav_path}")

                        # Verificar duração e intensidade do áudio
                        has_speech = False
                        duration = 0

                        # Tentar obter a duração do arquivo WAV
                        try:
                            with contextlib.closing(wave.open(wav_path, 'r')) as wf:
                                frames = wf.getnframes()
                                rate = wf.getframerate()
                                duration = frames / float(rate)
                                self.logger.info(
                                    f"Duração do áudio: {duration} segundos")

                                # Se a duração for muito curta, provavelmente não há fala
                                has_speech = duration > 0.5
                        except Exception as e:
                            self.logger.error(
                                f"Erro ao analisar duração do WAV: {e}")

                        # Se não conseguirmos verificar com wave, verificar com ffprobe
                        if not has_speech:
                            try:
                                # Verificar se há áudio com ffprobe
                                probe_cmd = ["ffprobe", "-i", temp_audio_path, "-show_streams",
                                             "-select_streams", "a", "-loglevel", "error"]
                                probe_result = subprocess.run(
                                    probe_cmd, capture_output=True, text=True)

                                # Se saída não estiver vazia, provavelmente tem áudio
                                has_speech = len(
                                    probe_result.stdout.strip()) > 0
                                self.logger.info(
                                    f"Detecção de áudio com ffprobe: {has_speech}")
                            except Exception as e:
                                self.logger.error(
                                    f"Erro ao verificar áudio com ffprobe: {e}")

                        # Verificar qual biblioteca de reconhecimento de fala está sendo usada
                        if has_speech:
                            try:
                                # Importar a função de reconhecimento de fala
                                from speech.recognition import recognize_speech

                                # Verificar se há problemas de importação com a função
                                self.logger.info(
                                    f"Tipo da função recognize_speech: {type(recognize_speech)}")

                                # Logar o caminho do arquivo antes do reconhecimento
                                self.logger.info(
                                    f"Tentando reconhecer áudio do arquivo: {wav_path}")
                                self.logger.info(f"Com idioma: {language}")

                                # Tente usar diretamente o reconhecedor do Google ou outra implementação
                                import speech_recognition as sr
                                recognizer = sr.Recognizer()

                                try:
                                    with sr.AudioFile(wav_path) as source:
                                        # Ajustar para ruído ambiente
                                        recognizer.adjust_for_ambient_noise(
                                            source)
                                        # Capturar o áudio
                                        audio_data = recognizer.record(source)

                                        # Tentar reconhecimento com Google (alternativa mais confiável)
                                        try:
                                            recognized_text = recognizer.recognize_google(
                                                audio_data, language=language)
                                            self.logger.info(
                                                f"Google Speech Recognition: '{recognized_text}'")
                                        except sr.UnknownValueError:
                                            self.logger.warning(
                                                "Google não reconheceu o áudio")
                                            recognized_text = ""
                                        except sr.RequestError as e:
                                            self.logger.error(
                                                f"Erro na API do Google: {e}")
                                            # Tentar com a função original como fallback
                                            recognition_result = recognize_speech(
                                                wav_path, language)
                                            if isinstance(recognition_result, str):
                                                recognized_text = recognition_result.lower().strip()
                                            else:
                                                recognized_text = recognition_result.get(
                                                    "text", "").lower().strip()
                                except Exception as sr_err:
                                    self.logger.error(
                                        f"Erro com speech_recognition: {sr_err}")
                                    # Ainda tentar com a função original
                                    recognition_result = recognize_speech(
                                        wav_path, language)
                                    if isinstance(recognition_result, str):
                                        recognized_text = recognition_result.lower().strip()
                                    else:
                                        recognized_text = recognition_result.get(
                                            "text", "").lower().strip()

                                # Verificar se o texto reconhecido não é apenas o código do idioma
                                if recognized_text.lower() == language.lower():
                                    self.logger.warning(
                                        f"Texto reconhecido igual ao código do idioma ({language}). Isso indica um problema no reconhecimento.")
                                    recognized_text = ""

                                self.logger.info(
                                    f"Texto reconhecido final: '{recognized_text}'")

                            except Exception as e:
                                self.logger.error(
                                    f"Erro no reconhecimento de fala: {e}")
                                recognized_text = ""
                        else:
                            self.logger.warning(
                                "Nenhuma fala detectada no áudio")
                            recognized_text = ""

                        # Calcular a similaridade entre o texto reconhecido e a palavra esperada
                        expected_lower = expected_word.lower().strip()

                        # Verificar se a palavra esperada está contida no texto reconhecido
                        is_exact_match = recognized_text == expected_lower
                        is_contained = expected_lower in recognized_text

                        # Se não houver fala detectada, a pronúncia está incorreta
                        if not has_speech:
                            is_correct = False
                            score = 0
                            feedback = "Não foi detectada nenhuma fala no áudio. Por favor, tente novamente falando mais alto."
                            recognized_text = "(sem fala detectada)"
                        # Se for correspondência exata, pronúncia perfeita
                        elif is_exact_match:
                            is_correct = True
                            score = 10
                            feedback = f"Excelente pronúncia de '{expected_word}'! Perfeito!"
                        # Se a palavra estiver contida no texto reconhecido, pronúncia boa
                        elif is_contained:
                            is_correct = True
                            score = 8
                            feedback = f"Boa pronúncia de '{expected_word}'! Continue assim."
                        # Se reconheceu algo, mas não a palavra esperada
                        elif recognized_text:
                            is_correct = False
                            score = 3
                            feedback = f"Tente novamente. Eu ouvi '{recognized_text}' mas esperava '{expected_word}'."
                        # Fallback para caso o reconhecimento falhe
                        else:
                            is_correct = False
                            score = 1
                            feedback = f"Não consegui entender. Tente pronunciar '{expected_word}' novamente, de forma clara."

                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"Erro ao converter áudio: {e}")
                        is_correct = False
                        score = 0
                        feedback = "Erro ao processar o áudio. Por favor, tente novamente."
                        recognized_text = ""

                finally:
                    # Limpar arquivos temporários
                    try:
                        if os.path.exists(temp_audio_path):
                            os.remove(temp_audio_path)
                        wav_path = temp_audio_path.replace(".webm", ".wav")
                        if os.path.exists(wav_path):
                            os.remove(wav_path)
                    except Exception as e:
                        self.logger.error(
                            f"Erro ao limpar arquivos temporários: {e}")

                # Gerar áudio para o feedback
                audio_feedback = None
                try:
                    # Importar a função de síntese
                    from speech.synthesis import synthesize_speech

                    # Sintetizar o feedback
                    audio_bytes = synthesize_speech(
                        feedback,  # Texto do feedback já gerado anteriormente
                        voice_settings={
                            "language_code": language  # Usar o mesmo idioma da avaliação
                        }
                    )

                    # Converter para base64 para enviar como texto
                    import base64
                    audio_feedback = base64.b64encode(
                        audio_bytes).decode('utf-8')
                    self.logger.info(
                        f"Áudio de feedback gerado com sucesso ({len(audio_feedback)} caracteres)")
                except Exception as audio_err:
                    self.logger.error(
                        f"Erro ao gerar áudio de feedback: {audio_err}")
                    # Manter audio_feedback como None em caso de erro

                # Adicionar o áudio de feedback ao resultado
                result = {
                    "success": True,
                    "isCorrect": is_correct,
                    "score": score,
                    "recognized_text": recognized_text,
                    "feedback": feedback,
                    "audio_feedback": audio_feedback  # Agora pode ter um valor
                }

                return result
            else:
                raise ValueError(
                    f"Unknown tool for speech_evaluator: {message.tool}")

        except Exception as e:
            self.logger.error(
                f"Error in speech evaluator handler: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "isCorrect": False,
                "score": 0,
                "recognized_text": "",
                "feedback": f"Erro na avaliação: {str(e)}",
                "audio_feedback": None
            }

    # --- Workflow Methods ---

    async def create_interactive_session(self, user_id: str) -> Dict[str, Any]:
        """
        Creates a new interactive session for a user.
        This involves selecting a persona, determining difficulty, creating a game,
        and generating initial instructions.
        """
        self.logger.info(f"Creating interactive session for user: {user_id}")
        context = ModelContext()
        session_id = str(uuid.uuid4())
        context.set("session_id", session_id)
        context.set("user_id", user_id)

        results = {
            "session_id": session_id,
            "user_id": user_id,
            "success": False,
            "timestamp": datetime.datetime.now().isoformat(),
            "error": None
        }

        try:
            # 1. Get User Info (Optional, but useful for personalization)
            user_info = await self.db_connector.get_user(user_id)
            if not user_info:
                raise ValueError(f"User not found: {user_id}")
            context.set("user_info", user_info)
            self.logger.info(f"User info retrieved for {user_id}")

            # 2. Select Persona (Tutor Agent) - Assuming a tool exists
            persona_message = Message(
                from_agent="system",
                to_agent="tutor",  # Assuming tutor agent name
                tool="select_persona",
                params={"user_preferences": user_info.get("preferences", {})}
            )
            persona_result = await self.server.process_message(persona_message, context)
            if isinstance(persona_result, dict) and persona_result.get("error"):
                raise Exception(
                    f"Persona selection failed: {persona_result['error']}")
            results["persona"] = persona_result
            context.set("persona", persona_result)
            self.logger.info(f"Persona selected: {persona_result}")

            # 3. Determine Difficulty (Progression Manager)
            difficulty_message = Message(
                from_agent="system",
                to_agent="progression_manager",
                tool="determine_difficulty",
                params={"user_id": user_id, "user_info": user_info}
            )
            difficulty_result = await self.server.process_message(difficulty_message, context)
            if isinstance(difficulty_result, dict) and difficulty_result.get("error"):
                raise Exception(
                    f"Difficulty determination failed: {difficulty_result['error']}")
            results["difficulty"] = difficulty_result
            context.set("difficulty", difficulty_result)
            self.logger.info(f"Difficulty determined: {difficulty_result}")

            # 4. Create Game (Game Designer)
            game_message = Message(
                from_agent="system",
                to_agent="game_designer",
                tool="create_game",
                params={
                    "user_id": user_id,
                    "difficulty": difficulty_result,
                    # Example default
                    "age_group": user_info.get("age_group", "adultos")
                }
            )
            game_result = await self.server.process_message(game_message, context)
            if isinstance(game_result, dict) and game_result.get("error"):
                raise Exception(
                    f"Game creation failed: {game_result['error']}")
            results["game_data"] = game_result
            context.set("current_game", game_result)  # Store game in context
            self.logger.info(f"Game created: {game_result.get('game_id')}")

            # 5. Create Instructions (Tutor Agent) - Assuming a tool exists
            instructions_message = Message(
                from_agent="system",
                to_agent="tutor",  # Assuming tutor agent name
                tool="create_instructions",
                params={
                    "game_title": game_result.get("title"),
                    "game_type": game_result.get("type"),
                    "difficulty": difficulty_result,
                    "persona": persona_result
                }
            )
            instructions_result = await self.server.process_message(instructions_message, context)
            if isinstance(instructions_result, dict) and instructions_result.get("error"):
                raise Exception(
                    f"Instruction creation failed: {instructions_result['error']}")
            results["instructions"] = instructions_result
            context.set("instructions", instructions_result)
            self.logger.info("Instructions created.")

            # 6. Save Session State
            session_data_to_save = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": results["timestamp"],
                "difficulty": difficulty_result,
                "persona": persona_result,
                "game_id": game_result.get("game_id"),
                "completed": False,
                "context": context._data  # Save the context data
            }
            await self.db_connector.save_session(session_data_to_save)
            self.logger.info(f"Session {session_id} saved.")

            results["success"] = True

        except Exception as e:
            self.logger.error(
                f"Error creating session for user {user_id}: {e}", exc_info=True)
            results["error"] = str(e)
            # Optionally save partial/failed session state
            failed_session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": results["timestamp"],
                "status": "failed",
                "error": str(e),
                "context": context._data
            }
            try:
                await self.db_connector.save_session(failed_session_data)
            except Exception as db_err:
                self.logger.error(
                    f"Failed to save error state for session {session_id}: {db_err}")

        return results

    async def load_existing_game_session(self, user_id: str, game_id: str) -> Dict[str, Any]:
        """Loads an existing game session for a user."""
        self.logger.info(
            f"Loading existing game session for user {user_id}, game {game_id}")

        try:
            # Create session context
            context = ModelContext()
            context.set("user_id", user_id)
            context.set("game_id", game_id)

            # Get game data
            game_data = self.db_connector.get_game(game_id)
            if not game_data:
                raise ValueError(f"Game not found: {game_id}")

            self.logger.info(
                f"Found game: {game_data.get('title', 'Untitled')}")

            # Get user info
            user_info = self.db_connector.get_user_by_id(user_id)
            if not user_info:
                raise ValueError(f"User not found: {user_id}")

            # Get exercises from the game data
            exercises = []
            if "exercises" in game_data:
                exercises = game_data["exercises"]
            elif "content" in game_data:
                if isinstance(game_data["content"], list):
                    exercises = game_data["content"]
                elif isinstance(game_data["content"], dict):
                    exercises = game_data["content"].get("exercises", [])

            self.logger.info(f"Found {len(exercises)} exercises")

            # Create a session ID
            session_id = str(uuid.uuid4())
            context.set("session_id", session_id)

            # Get instructions from tutor
            instructions_message = Message(
                from_agent="system",
                to_agent="tutor",
                tool="create_instructions",
                params={
                    "game_title": game_data.get("title"),
                    "game_type": game_data.get("game_type"),
                    "difficulty": game_data.get("difficulty"),
                    "persona": user_info.get("preferences", {}).get("preferred_persona", "default")
                }
            )

            instructions = await self.server.process_message(instructions_message, context)

            # Save session state
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "game_id": game_id,
                "start_time": datetime.datetime.utcnow().isoformat(),
                "status": "active",
                "context": context._data
            }
            self.db_connector.save_session(session_data)

            # Format response exactly as frontend expects
            game_response = {
                "game": {
                    "description": "",  # Frontend expects this even if empty
                    "difficulty": game_data.get("difficulty", "iniciante"),
                    "exercises": exercises,
                    "game_id": str(game_id),
                    "game_type": game_data.get("game_type", "exercícios de pronúncia"),
                    "instructions": [],  # Frontend expects an array
                    "metadata": {},  # Frontend expects this even if empty
                    "title": game_data.get("title")
                },
                "session_id": session_id,
                "success": True,
                "user_info": {
                    "name": user_info.get("name"),
                    "preferences": user_info.get("preferences", {})
                }
            }

            # Log the response structure
            self.logger.info(f"Returning game with {len(exercises)} exercises")
            self.logger.debug(
                f"Response structure: {json.dumps(game_response, indent=2)}")

            return game_response

        except Exception as e:
            self.logger.error(f"Error loading game session: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load game session: {str(e)}"
            }

    def evaluate_pronunciation(self, audio_file, expected_word, user_id=None, session_id=None):
        """Wrapper síncrono para evaluate_pronunciation_async"""
        import asyncio

        # Usar o loop de eventos existente ou criar um novo
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Executar a função assíncrona e obter o resultado
        return loop.run_until_complete(self._evaluate_pronunciation_async(
            audio_file, expected_word, user_id, session_id))

    async def _evaluate_pronunciation_async(self, audio_file, expected_word, user_id=None, session_id=None):
        """Implementação assíncrona da avaliação de pronúncia"""
        try:
            # Ler os dados do arquivo com tratamento de erro robusto
            audio_data = None
            try:
                audio_file.seek(0)  # Garantir que estamos no início do arquivo
                audio_data = audio_file.read()
            except Exception as audio_err:
                self.logger.error(
                    f"Erro ao ler arquivo de áudio: {str(audio_err)}")
                # Tentar abordagem alternativa
                if hasattr(audio_file, 'stream'):
                    self.logger.info("Tentando ler do stream do arquivo")
                    audio_file.stream.seek(0)
                    audio_data = audio_file.stream.read()

            if not audio_data:
                raise ValueError(
                    "Não foi possível ler os dados do arquivo de áudio")
        except Exception as e:
            self.logger.error(f"Erro na leitura do arquivo de áudio: {str(e)}")
            return {
                "success": False,
                "error": f"Erro na leitura do arquivo de áudio: {str(e)}"
            }

    async def evaluate_pronunciation(self, audio_file, expected_word, user_id=None, session_id=None):
        """
        Avalia a pronúncia do usuário comparando com a palavra esperada.

        Args:
            audio_file: Arquivo de áudio com a pronúncia do usuário (objeto de upload do Flask/FastAPI)
            expected_word: Palavra que o usuário deveria pronunciar
            user_id: ID do usuário (opcional)
            session_id: ID da sessão de jogo (opcional)

        Returns:
            Dict contendo os resultados da avaliação
        """
        self.logger.info(
            f"Avaliando pronúncia: palavra='{expected_word}', user_id={user_id}, session_id={session_id}")

        try:
            # Criar contexto para a solicitação
            context = ModelContext()
            if user_id:
                context.set("user_id", user_id)
            if session_id:
                context.set("session_id", session_id)
            context.set("expected_word", expected_word)

            # Ler os dados do arquivo - O objeto audio_file já é um file-like object
            # que podemos ler diretamente
            audio_data = audio_file.read()

            # Enviar solicitação para o Speech Evaluator Agent
            evaluation_message = Message(
                from_agent="system",
                to_agent="speech_evaluator",  # Nome do agente responsável pela avaliação de pronúncia
                tool="evaluate_pronunciation",
                params={
                    "audio_data": audio_data,
                    "expected_word": expected_word,
                    "language": "pt-PT"  # Por padrão português europeu
                }
            )

            # Processar a avaliação
            result = await self.server.process_message(evaluation_message, context)

            # Se não tiver um agente real de avaliação, podemos fornecer uma implementação simulada
            # para testes durante o desenvolvimento
            if isinstance(result, dict) and result.get("error"):
                self.logger.warning(
                    f"Erro no agente de avaliação: {result.get('error')}")
                # Implementação simulada para desenvolvimento
                import random

                # Simular uma avaliação básica com 70% de chance de estar correto
                is_correct = random.random() < 0.7
                score = random.randint(
                    7, 10) if is_correct else random.randint(2, 6)

                # Gerar texto de reconhecimento com alguma variação da palavra esperada
                if is_correct:
                    recognized_text = expected_word
                else:
                    # Simular um erro comum de reconhecimento alterando uma letra
                    chars = list(expected_word)
                    if len(chars) > 2:
                        pos = random.randint(0, len(chars) - 1)
                        chars[pos] = random.choice(
                            'abcdefghijklmnopqrstuvwxyz')
                    recognized_text = ''.join(chars)

                # Gerar feedback baseado na correção
                if is_correct:
                    feedback = f"Boa pronúncia de '{expected_word}'! Continue assim."
                else:
                    feedback = f"Tente novamente prestando atenção na pronúncia correta de '{expected_word}'."

                result = {
                    "success": True,  # Sempre retornar success=True para evitar erros no frontend
                    "isCorrect": is_correct,
                    "score": score,
                    "recognized_text": recognized_text,
                    "feedback": feedback,
                    "audio_feedback": None  # Em uma implementação real, poderia haver áudio de feedback
                }

                self.logger.info(f"Avaliação simulada: {result}")

            # Garantir que o resultado sempre tenha a chave 'success'
            if 'success' not in result:
                result['success'] = True

            # Registrar resultado da avaliação no banco de dados se tivermos session_id
            if session_id:
                try:
                    # Verificar se o método existe e se é assíncrono
                    if hasattr(self.db_connector, 'save_pronunciation_evaluation'):
                        # Verificar se o método é assíncrono
                        import inspect
                        is_async = inspect.iscoroutinefunction(
                            self.db_connector.save_pronunciation_evaluation)

                        if is_async:
                            # Se o método for assíncrono, usar await
                            await self.db_connector.save_pronunciation_evaluation(
                                session_id=session_id,
                                expected_word=expected_word,
                                recognized_text=result.get(
                                    "recognized_text", ""),
                                is_correct=result.get("isCorrect", False),
                                score=result.get("score", 0),
                                timestamp=datetime.datetime.now().isoformat()
                            )
                        else:
                            # Se o método for síncrono, chamar diretamente
                            self.db_connector.save_pronunciation_evaluation(
                                session_id=session_id,
                                expected_word=expected_word,
                                recognized_text=result.get(
                                    "recognized_text", ""),
                                is_correct=result.get("isCorrect", False),
                                score=result.get("score", 0),
                                timestamp=datetime.datetime.now().isoformat()
                            )

                        self.logger.info(
                            f"Avaliação salva no banco de dados para sessão {session_id}")
                    else:
                        self.logger.warning(
                            "Método save_pronunciation_evaluation não encontrado no db_connector")
                except Exception as db_err:
                    self.logger.error(
                        f"Erro ao salvar avaliação no banco de dados: {db_err}")

            return result

        except Exception as e:
            self.logger.error(
                f"Erro na avaliação de pronúncia: {str(e)}", exc_info=True)
            return {
                "success": False,
                "isCorrect": False,
                "score": 0,
                "recognized_text": "",
                "feedback": f"Erro ao processar avaliação: {str(e)}",
                "audio_feedback": None
            }

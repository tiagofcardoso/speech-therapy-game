from typing import Dict, Any, Optional
import json
import logging
import os
from openai import OpenAI
from speech.synthesis import synthesize_speech

# Corrigir o formato do logging - havia um '%s' sem o valor correspondente
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class TutorAgent:
    def __init__(self, game_designer: 'GameDesignerAgent'):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.logger = logging.getLogger("TutorAgent")
        self.game_designer = game_designer
        self.user_sessions = {}
        self.voice_enabled = os.environ.get(
            "ENABLE_TUTOR_VOICE", "true").lower() == "true"
        self.logger.info(
            f"TutorAgent initialized with voice {'enabled' if self.voice_enabled else 'disabled'}")

    def create_instructions(self, user_profile: Dict[str, Any], difficulty: str) -> Dict[str, Any]:
        name = user_profile.get("name", "amigo")
        age = user_profile.get("age", 7)
        try:
            prompt = f"Crie instruções em português para {name}, {age} anos, nível {difficulty}. Retorne JSON com 'greeting', 'explanation', 'encouragement'."

            # Try with gpt-4o-mini first
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system",
                            "content": "És um terapeuta da fala amigável."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                instructions = json.loads(response.choices[0].message.content)
            except Exception as e:
                self.logger.warning(f"Error with gpt-4o-mini: {str(e)}")
                # Fallback to gpt-4o-mini
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system",
                            "content": "És um terapeuta da fala amigável."},
                        {"role": "user", "content": prompt +
                            " Responda apenas com o objeto JSON, sem texto adicional."}
                    ]
                )
                try:
                    instructions = json.loads(
                        response.choices[0].message.content)
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse JSON from response")
                    # Default fallback if all else fails
                    instructions = {
                        "greeting": f"Olá, {name}!",
                        "explanation": "Vamos praticar palavras legais hoje!",
                        "encouragement": "Vais arrasar!"
                    }

            # Generate voice if enabled
            if self.voice_enabled:
                try:
                    # Configuração específica para o caráter do tutor
                    # Use voz feminina para o tutor com motor padrão (não neural)
                    voice_settings = {"voice_id": "Ines", "engine": "standard"}

                    greeting_audio = synthesize_speech(
                        instructions["greeting"], voice_settings)
                    explanation_audio = synthesize_speech(
                        instructions["explanation"], voice_settings)
                    encouragement_audio = synthesize_speech(
                        instructions["encouragement"], voice_settings)

                    if greeting_audio and explanation_audio and encouragement_audio:
                        instructions["audio"] = {
                            "greeting": greeting_audio,
                            "explanation": explanation_audio,
                            "encouragement": encouragement_audio
                        }
                    else:
                        self.logger.warning(
                            "Some audio segments failed to generate")
                except Exception as e:
                    self.logger.error(
                        f"Failed to generate voice for instructions: {str(e)}")

            return instructions

        except Exception as e:
            self.logger.error(f"Error creating instructions: {str(e)}")
            default_instructions = {
                "greeting": f"Olá, {name}!",
                "explanation": "Vamos praticar palavras legais hoje!",
                "encouragement": "Vais arrasar!"
            }

            if self.voice_enabled:
                try:
                    default_instructions["audio"] = {
                        "greeting": synthesize_speech(default_instructions["greeting"]),
                        "explanation": synthesize_speech(default_instructions["explanation"]),
                        "encouragement": synthesize_speech(default_instructions["encouragement"])
                    }
                except:
                    self.logger.error(
                        "Failed to generate voice for default instructions")

            return default_instructions

    def provide_feedback(self, user_id: str, response: str) -> Dict[str, Any]:
        current_exercise = self.game_designer.get_current_exercise(user_id)
        if not current_exercise:
            self.logger.warning(f"No active game for user {user_id}")
            error_message = "Nenhum jogo ativo encontrado para este utilizador"
            return {
                "error": error_message,
                "message": error_message,
                "audio": synthesize_speech(error_message) if self.voice_enabled else None
            }

        game_type = self.game_designer.current_games[user_id]["game_type"]
        expected = self._get_expected_word(current_exercise, game_type)

        evaluation = self._evaluate_pronunciation(response, expected)
        score = evaluation.get("score", 5)
        explanation = evaluation.get("explanation", "Avaliação padrão")

        feedback_text = self._generate_feedback(score, explanation, expected)
        self._update_user_progress(user_id, score)

        feedback = {
            "score": score,
            "message": feedback_text,
            "correct": score >= 7,
            "next_exercise": self.game_designer.get_current_exercise(user_id) is not None
        }

        # Add audio feedback if voice is enabled
        if self.voice_enabled:
            try:
                feedback["audio"] = synthesize_speech(feedback_text)
            except Exception as e:
                self.logger.error(f"Error generating voice feedback: {str(e)}")

        return feedback

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
            # Try with gpt-4o-mini which supports response_format
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "És um assistente de terapia da fala. Avalia a precisão da pronúncia."},
                        {"role": "user", "content": (
                            f"Palavra esperada: '{expected}'. Pronúncia do utilizador: '{actual}'. "
                            "Retorna um JSON com 'score' (1-10) e 'explanation' (string explicando o score)."
                        )}
                    ],
                    response_format={"type": "json_object"}
                )
                evaluation = json.loads(response.choices[0].message.content)
            except Exception as e:
                self.logger.error(f"Error with gpt-4o-mini: {str(e)}")
                # Fallback to gpt-4o-mini without response_format
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um assistente de terapia da fala. Avalie a precisão da pronúncia."},
                        {"role": "user", "content": (
                            f"Palavra esperada: '{expected}'. Pronúncia do usuário: '{actual}'. "
                            "Retorne um JSON com 'score' (1-10) e 'explanation' (string explicando o score). IMPORTANTE: responda somente o objeto JSON."
                        )}
                    ]
                )
                try:
                    evaluation = json.loads(
                        response.choices[0].message.content)
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse JSON response")
                    return {"score": 5, "explanation": "Avaliação padrão devido a erro no processamento"}

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
                    {"role": "system", "content": "És um terapeuta da fala amigável. Fornece feedback encorajador em português europeu."},
                    {"role": "user", "content": (
                        f"Dá feedback encorajador para alguém que tentou dizer '{expected}'. "
                        f"Avaliação: score={score}, explicação={explanation}. "
                        f"Usa português europeu (de Portugal, não do Brasil)."
                    )}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating feedback: {str(e)}")
            return f"Excelente tentativa com '{expected}'! Vamos praticar mais."

    def _update_user_progress(self, user_id: str, score: int):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"attempts": 0, "total_score": 0}
        self.user_sessions[user_id]["attempts"] += 1
        self.user_sessions[user_id]["total_score"] += score
        self.game_designer.update_progress(user_id, score)
        self.logger.info(
            f"Updated progress for {user_id}: attempts={self.user_sessions[user_id]['attempts']}, total_score={self.user_sessions[user_id]['total_score']}")

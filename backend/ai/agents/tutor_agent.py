from typing import Dict, Any, Optional, List
import json
import logging
import os
import random
import datetime
from openai import OpenAI
from speech.synthesis import synthesize_speech
from .base_agent import BaseAgent

# Configuração adequada do logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class TutorAgent(BaseAgent):
    def __init__(self, game_designer=None, client=None):
        super().__init__(client)
        self.game_designer = game_designer
        self.logger = logging.getLogger("TutorAgent")
        self.user_sessions = {}
        self.voice_enabled = os.environ.get(
            "ENABLE_TUTOR_VOICE", "true").lower() == "true"

        # Carregar personalidades do tutor
        self.tutor_personas = {
            "animado": {
                "voice": "Ines",  # Voz feminina animada
                "style": "entusiasta e energético",
                "emoji": "🌟",
                "encouragements": [
                    "Incrível trabalho!",
                    "Estás a dar o teu melhor!",
                    "Super esforço!",
                    "Continua assim, estás a arrasar!"
                ]
            },
            "calmo": {
                "voice": "Cristiano",  # Voz masculina calma
                "style": "tranquilo e paciente",
                "emoji": "😊",
                "encouragements": [
                    "Muito bem.",
                    "Estás no bom caminho.",
                    "Observo o teu progresso.",
                    "Cada passo conta, continua."
                ]
            },
            "engraçado": {
                "voice": "Ines",
                "style": "bem-humorado e divertido",
                "emoji": "😄",
                "encouragements": [
                    "Uau, és quase tão bom quanto eu! Haha!",
                    "Fantástico! És uma estrela da pronúncia!",
                    "Mais um acerto! Isto está a ficar divertido!",
                    "Cuidado, vais ficar melhor que o tutor!"
                ]
            }
        }

        # Configurações de voz
        self.voice_settings = {
            "Ines": {"voice_id": "Ines", "engine": "neural", "speed": 1.0},
            "Cristiano": {"voice_id": "Cristiano", "engine": "neural", "speed": 0.9}
        }

        # Histórico de interações para rastreamento de longo prazo
        self.interaction_history = {}

        self.logger.info(
            f"TutorAgent inicializado com voz {'ativada' if self.voice_enabled else 'desativada'}")

    async def create_instructions(self, user_profile: Dict[str, Any], difficulty: str) -> Dict[str, Any]:
        """Async version of create_instructions"""
        name = user_profile.get("name", "amigo")
        age = user_profile.get("age", 7)
        user_id = user_profile.get("id", "unknown")

        # Selecionar uma persona adequada à idade
        persona = self._select_persona_for_user(user_id, age)

        self.logger.info(
            f"TutorAgent.create_instructions chamado pelo coordenador MCP para usuário {user_id}")
        try:
            # Incluir contexto do usuário no prompt
            user_context = ""
            if user_id in self.interaction_history:
                sessions = self.interaction_history[user_id]["sessions"]
                if sessions:
                    last_session = sessions[-1]
                    user_context = f"Na última sessão em {last_session['date']}, {name} praticou {last_session['game_type']} com foco no som '{last_session['target_sound']}' e teve desempenho {last_session['performance']}."

            prompt = f"""
            Crie instruções em português de Portugal para {name}, {age} anos, nível {difficulty}.
            {user_context}
            Seja {persona['style']} em suas explicações.
            Retorne JSON com 'greeting', 'explanation', 'encouragement' e 'tips'.
            """

            # Try with gpt-4o-mini first
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system",
                            "content": f"És um terapeuta da fala {persona['style']} que trabalha com crianças."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=300
                )
                instructions = json.loads(response.choices[0].message.content)
            except Exception as e:
                self.logger.warning(f"Erro com gpt-4o-mini: {str(e)}")
                # Fallback to gpt-4o-mini
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system",
                            "content": f"És um terapeuta da fala {persona['style']} que trabalha com crianças."},
                        {"role": "user", "content": prompt +
                            " Responda apenas com o objeto JSON, sem texto adicional."}
                    ],
                    max_tokens=300
                )
                try:
                    instructions = json.loads(
                        response.choices[0].message.content)
                except json.JSONDecodeError:
                    self.logger.warning("Falha ao analisar JSON da resposta")
                    # Default fallback if all else fails
                    instructions = {
                        "greeting": f"Olá, {name}! {persona['emoji']}",
                        "explanation": f"Hoje vamos praticar alguns sons divertidos no nível {difficulty}!",
                        "encouragement": random.choice(persona["encouragements"]),
                        "tips": ["Respira fundo antes de falar", "Tenta falar devagar e com clareza", "Diverte-te!"]
                    }

            # Adicionar elementos da persona
            instructions["greeting"] = f"{instructions['greeting']} {persona['emoji']}"

            # Generate voice if enabled
            if self.voice_enabled:
                try:
                    # Usar configurações de voz da persona
                    voice_settings = self.voice_settings.get(persona["voice"],
                                                             {"voice_id": "Ines", "engine": "neural"})

                    greeting_audio = await self._synthesize_speech_async(
                        instructions["greeting"], voice_settings)
                    explanation_audio = await self._synthesize_speech_async(
                        instructions["explanation"], voice_settings)
                    encouragement_audio = await self._synthesize_speech_async(
                        instructions["encouragement"], voice_settings)

                    # Sintetizar dicas opcionais
                    tips_audio = None
                    if "tips" in instructions and isinstance(instructions["tips"], list) and instructions["tips"]:
                        tips_text = ". ".join(instructions["tips"])
                        tips_audio = await self._synthesize_speech_async(
                            tips_text, voice_settings)

                    if greeting_audio and explanation_audio and encouragement_audio:
                        instructions["audio"] = {
                            "greeting": greeting_audio,
                            "explanation": explanation_audio,
                            "encouragement": encouragement_audio
                        }
                        if tips_audio:
                            instructions["audio"]["tips"] = tips_audio
                    else:
                        self.logger.warning(
                            "Alguns segmentos de áudio falharam na geração")
                except Exception as e:
                    self.logger.error(
                        f"Falha ao gerar voz para instruções: {str(e)}")

            # Armazenar contexto da sessão para uso futuro
            self._record_session_start(user_id, difficulty)

            return instructions

        except Exception as e:
            self.logger.error(f"Erro ao criar instruções: {str(e)}")
            default_instructions = {
                "greeting": f"Olá, {name}! {persona['emoji']}",
                "explanation": "Vamos praticar palavras divertidas hoje!",
                "encouragement": random.choice(persona["encouragements"]),
                "tips": ["Respira fundo", "Fala devagar", "Diverte-te!"]
            }

            if self.voice_enabled:
                try:
                    voice_settings = self.voice_settings.get(persona["voice"],
                                                             {"voice_id": "Ines", "engine": "neural"})

                    default_instructions["audio"] = {
                        "greeting": await self._synthesize_speech_async(default_instructions["greeting"], voice_settings),
                        "explanation": await self._synthesize_speech_async(default_instructions["explanation"], voice_settings),
                        "encouragement": await self._synthesize_speech_async(default_instructions["encouragement"], voice_settings)
                    }
                except Exception as e:
                    self.logger.error(
                        f"Falha ao gerar voz para instruções padrão: {str(e)}")

            return default_instructions

    async def _synthesize_speech_async(self, text, voice_config):
        """Async wrapper around speech synthesis"""
        from speech.synthesis import synthesize_speech_async
        return await synthesize_speech_async(text, voice_config)

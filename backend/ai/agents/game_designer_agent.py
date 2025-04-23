from typing import Optional, Dict, List, Any
import random
import json
import logging
import datetime
import uuid
from ..server.openai_client import create_async_openai_client  # Updated import
from openai import AsyncOpenAI  # Direct import for type hints
import os
from pathlib import Path
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class GameDesignerAgent(BaseAgent):
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self.client = client or create_async_openai_client()
        self.logger = logging.getLogger(__name__)

    async def create_game(self, user_id: str, difficulty: str = "iniciante",
                          game_type: str = "exercícios de pronúncia") -> Dict[str, Any]:
        """Creates a new game for the user using LLM"""
        try:
            # Criar prompt para o LLM
            prompt = self._create_game_prompt(game_type, difficulty)

            # Obter resposta do modelo usando o cliente async
            completion = await self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "Você é um especialista em criar jogos educativos para terapia da fala."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            # Processar resposta
            game_data = json.loads(completion.choices[0].message.content)

            # Adicionar metadados
            game_data.update({
                "game_id": str(uuid.uuid4()),
                "user_id": user_id,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "status": "active",
                "game_type": game_type,
                "difficulty": difficulty
            })

            return game_data

        except Exception as e:
            self.logger.error(f"Error creating game: {str(e)}")
            raise

    def _create_game_prompt(self, game_type: str, difficulty: str) -> str:
        """Creates the prompt for game generation"""
        return f"""
        Crie um jogo do tipo '{game_type}' com dificuldade '{difficulty}'.
        O jogo deve ter:
        - Um título criativo
        - 5 exercícios adequados ao nível
        - Dicas e instruções claras
        - Feedback construtivo

        Retorne no formato JSON com a seguinte estrutura:
        {{
            "title": "string",
            "game_type": "string",
            "difficulty": "string",
            "exercises": [
                {{
                    "word": "string",
                    "prompt": "string",
                    "hint": "string",
                    "type": "string",
                    "feedback": {{}}
                }}
            ]
        }}
        """

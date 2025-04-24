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
from utils.language_utils import get_pt_avoid_examples

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class GameDesignerAgent(BaseAgent):
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self.client = client or create_async_openai_client()
        self.logger = logging.getLogger(__name__)
        # Load PT-PT/PT-BR language examples when initializing
        self.pt_avoid_examples = get_pt_avoid_examples(max_examples=15)
        self.logger.info(
            "Loaded PT-PT/PT-BR language examples for improved prompting")

    async def create_game(self, user_id: str, difficulty: str = "iniciante",
                          game_type: str = "exercícios de pronúncia",
                          language: str = "pt-PT") -> Dict[str, Any]:
        """Creates a new game for the user using LLM"""
        try:
            # Criar prompt para o LLM
            prompt = self._create_game_prompt(game_type, difficulty, language)

            # Log the difficulty and game type for debugging
            self.logger.info(
                f"Creating game for user {user_id} with difficulty: {difficulty}, type: {game_type}")

            # Create enhanced system prompt with PT-PT guidance
            system_prompt = f"""És um especialista em fonoaudiologia e terapia da fala que cria jogos educativos para crianças e adultos em português europeu (PT-PT).

Ao criar jogos para terapia da fala, considera sempre:
1. Usar EXCLUSIVAMENTE português europeu (de Portugal, não do Brasil)
2. Adaptar exercícios ao nível de desenvolvimento fonológico do utilizador
3. Focar em sons problemáticos específicos (R, L, S, grupos consonantais)
4. Criar exercícios que sejam envolventes e adequados para a idade

IMPORTANTE - DIFERENÇAS ENTRE PORTUGUÊS EUROPEU E BRASILEIRO:
Use APENAS palavras e expressões de Portugal (PT-PT), evitando brasileirismos (PT-BR).
{self.pt_avoid_examples}

Para cada nível de dificuldade:
- INICIANTE: Palavras curtas (1-2 sílabas), sons simples, vocabulário básico do quotidiano
- MÉDIO: Palavras com 2-3 sílabas, alguns encontros consonantais, distinção de sons semelhantes
- AVANÇADO: Palavras complexas, frases completas, trava-línguas, narrativas curtas

O conteúdo DEVE ser:
- Culturalmente relevante para Portugal
- Pedagogicamente validado
- Motivador e recompensador
- Progressivo em dificuldade

Formata todos os jogos em JSON limpo e válido, com exercícios claros, instruções detalhadas e feedback construtivo."""

            # Obter resposta do modelo usando o cliente async
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
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

    def _create_game_prompt(self, game_type: str, difficulty: str, language: str = "pt-PT") -> str:
        """Creates the prompt for game generation"""
        # Enhance prompt to be more specific about the difficulty level
        difficulty_details = {
            "iniciante": "para crianças ou iniciantes, utilizando palavras simples e sons básicos, fácil de pronunciar",
            "médio": "para um nível intermediário, utilizando palavras com mais sílabas e alguns encontros consonantais",
            "avançado": "para um nível avançado, utilizando palavras complexas, trava-línguas, e exercícios com frases completas"
        }

        # Get the appropriate difficulty description or use a default
        difficulty_desc = difficulty_details.get(
            difficulty, "adaptado ao nível do utilizador")

        return f"""
        Crie um jogo do tipo '{game_type}' com dificuldade '{difficulty}' ({difficulty_desc}).
        O jogo deve ser em português europeu (PT-PT) e ter:
        - Um título criativo relacionado com o tema
        - 5 exercícios adaptados ao nível de dificuldade {difficulty}
        - Dicas e instruções claras
        - Feedback construtivo específico para cada exercício
        
        Para o nível {difficulty}, utilize o vocabulário e complexidade apropriados.
        As palavras devem ser reais, de uso comum em Portugal, e adequadas para terapia da fala.
        
        Retorne no formato JSON com a seguinte estrutura:
        {{
            "title": "string em português",
            "game_type": "string em português",
            "difficulty": "string em português",
            "exercises": [
                {{
                    "word": "palavra em português apropriada para o nível {difficulty}",
                    "prompt": "instrução clara em português",
                    "hint": "dica útil em português",
                    "type": "tipo de exercício em português",
                    "feedback": {{
                        "correct": "feedback positivo em português",
                        "incorrect": "feedback construtivo em português"
                    }}
                }}
            ]
        }}
        """

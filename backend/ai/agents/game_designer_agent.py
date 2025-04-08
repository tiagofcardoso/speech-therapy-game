from typing import Optional, Dict, List, Any
import random
import json
import logging
import datetime
from ..server.openai_client import create_openai_client

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class GameDesignerAgent:
    def __init__(self):
        self.client = create_openai_client()
        self.logger = logging.getLogger("GameDesignerAgent")
        self.game_types = ["palavras cruzadas", "adivinhações",
                           "rimas", "exercícios de pronúncia", "desafios de pronúncia"]
        self.difficulty_levels = ["iniciante", "médio", "avançado"]
        self.target_sounds = ["s", "r", "l", "p",
                              "t", "ch", "j", "m", "n", "lh", "nh"]
        self.current_games = {}
        self.logger.info("GameDesignerAgent initialized")

    def create_game(self, user_id: str, difficulty: Optional[str] = None, game_type: Optional[str] = None,
                    age_group: Optional[str] = "crianças") -> Dict[str, Any]:
        difficulty = difficulty if difficulty in self.difficulty_levels else self._get_user_difficulty(
            user_id)
        game_type = game_type if game_type in self.game_types else self._get_appropriate_game_type(
            user_id)
        age_group = age_group if age_group in [
            "crianças", "adultos"] else "crianças"

        self.logger.info(
            f"Creating game for user {user_id}: difficulty={difficulty}, type={game_type}, age_group={age_group}")

        game_content = self._generate_content(difficulty, game_type, age_group)
        game_id = f"{random.randint(1000, 9999)}-{user_id}"

        self.current_games[user_id] = {
            "game_id": game_id,
            "difficulty": difficulty,
            "game_type": game_type,
            "age_group": age_group,
            "content": game_content,
            "current_index": 0,
            "score": 0,
            "created_at": datetime.datetime.now().isoformat()
        }

        return {
            "game_id": game_id,
            "difficulty": difficulty,
            "game_type": game_type,
            "title": game_content.get("title", f"Jogo de {game_type.capitalize()}"),
            "description": game_content.get("description", "Exercício de terapia da fala"),
            "instructions": game_content.get("instructions", ["Siga as instruções do jogo"]),
            "content": game_content.get("exercises", []),
            "metadata": {
                "target_skills": game_content.get("target_skills", []),
                "target_sound": game_content.get("target_sound", "variado"),
                "estimated_duration": game_content.get("estimated_duration", "5-10 minutos")
            }
        }

    def get_current_exercise(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id not in self.current_games:
            return None
        game = self.current_games[user_id]
        current_index = game["current_index"]
        exercises = game["content"]["exercises"]
        if current_index < len(exercises):
            return exercises[current_index]
        return None

    def update_progress(self, user_id: str, score_increment: int):
        if user_id in self.current_games:
            self.current_games[user_id]["score"] += score_increment
            self.current_games[user_id]["current_index"] += 1
            self.logger.info(
                f"Updated progress for {user_id}: score={self.current_games[user_id]['score']}, index={self.current_games[user_id]['current_index']}")

    def _get_user_difficulty(self, user_id: str) -> str:
        if user_id in self.current_games and self.current_games[user_id]["score"] > 50:
            return "médio"
        elif user_id in self.current_games and self.current_games[user_id]["score"] > 100:
            return "avançado"
        return "iniciante"

    def _get_appropriate_game_type(self, user_id: str) -> str:
        return random.choice(self.game_types)

    def _generate_content(self, difficulty: str, game_type: str, age_group: str) -> Dict[str, Any]:
        try:
            if not self.client:
                self.logger.warning(
                    "OpenAI client unavailable. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group)

            system_prompt = self._create_system_prompt(
                game_type, difficulty, age_group)
            target_sound = random.choice(self.target_sounds)

            user_prompt = (
                f"Crie um jogo de terapia da fala do tipo '{game_type}' em português para {age_group}, "
                f"nível '{difficulty}', focado no som '{target_sound}'. "
                "Inclua um título criativo, descrição, instruções claras (em lista), 5 exercícios e metadados. "
                "Retorne como um objeto JSON com as chaves: 'title', 'description', 'instructions' (lista), "
                "'exercises' (lista), 'target_skills' (lista), 'target_sound' (string), 'estimated_duration' (string)."
            )

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )

            content_json = json.loads(response.choices[0].message.content)
            required_keys = ["title", "description",
                             "instructions", "exercises", "target_sound"]
            if not all(key in content_json for key in required_keys):
                self.logger.warning(
                    "Incomplete OpenAI response. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group)

            self.logger.info(f"Generated game: {content_json['title']}")
            return content_json
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return self._get_fallback_content(game_type, difficulty, age_group)

    def _create_system_prompt(self, game_type: str, difficulty: str, age_group: str) -> str:
        base_prompt = f"""Você é um especialista em terapia da fala para {age_group} falantes de português.

# CONTEXTO
Você está criando jogos para uma aplicação de terapia da fala que ajuda {age_group} a melhorar suas habilidades de comunicação.
O jogo deve ser adequado para o nível de dificuldade '{difficulty}' e focar no tipo '{game_type}'.

# FORMATO DE SAÍDA
Responda com um objeto JSON contendo:
- "title": título criativo do jogo
- "description": breve descrição do objetivo
- "instructions": lista de instruções claras
- "exercises": lista com 5 exercícios específicos
- "target_skills": lista de habilidades desenvolvidas
- "target_sound": som-alvo do jogo (ex.: "s", "r")
- "estimated_duration": tempo estimado (ex.: "5-10 minutos")
"""
        if game_type == "palavras cruzadas":
            return base_prompt + """
# TIPO: PALAVRAS CRUZADAS
Cada exercício deve ter: "clue" (dica), "word" (palavra), "position" (horizontal/vertical).
"""
        elif game_type == "adivinhações":
            return base_prompt + """
# TIPO: ADIVINHAÇÕES
Cada exercício deve ter: "clue" (dica), "answer" (resposta).
"""
        elif game_type == "rimas":
            return base_prompt + """
# TIPO: RIMAS
Cada exercício deve ter: "starter" (palavra inicial), "rhymes" (lista de rimas).
"""
        elif game_type == "exercícios de pronúncia":
            return base_prompt + """
# TIPO: EXERCÍCIOS DE PRONÚNCIA
Cada exercício deve ter: "word" (palavra), "tip" (dica de pronúncia).
"""
        elif game_type == "desafios de pronúncia":
            return base_prompt + """
# TIPO: DESAFIOS DE PRONÚNCIA
Cada exercício deve ter: "sentence" (frase), "challenge" (desafio específico).
"""

    def _get_fallback_content(self, game_type: str, difficulty: str, age_group: str) -> Dict[str, Any]:
        target_sound = random.choice(self.target_sounds)
        if game_type == "exercícios de pronúncia":
            return {
                "title": "Sons Simples",
                "description": "Pratique o som-alvo com palavras fáceis.",
                "instructions": ["Diga cada palavra em voz alta."],
                "exercises": [
                    {"word": "sol", "tip": "Destaque o 's'"},
                    {"word": "sapo", "tip": "Foco no 's'"}
                ],
                "target_skills": ["articulação"],
                "target_sound": "s",
                "estimated_duration": "5 minutos"
            }
        return {
            "title": f"Jogo de {game_type.capitalize()}",
            "description": "Pratique o som-alvo.",
            "instructions": ["Diga as palavras em voz alta."],
            "exercises": [{"word": "sol", "tip": "Destaque o 's'"}],
            "target_skills": ["articulação"],
            "target_sound": "s",
            "estimated_duration": "5 minutos"
        }

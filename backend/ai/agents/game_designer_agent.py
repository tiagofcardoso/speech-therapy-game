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
        # Se o parâmetro de dificuldade for "aleatório" ou None, escolha aleatoriamente
        if difficulty is None or difficulty == "aleatório":
            difficulty = random.choice(self.difficulty_levels)
        elif difficulty not in self.difficulty_levels:
            difficulty = self._get_user_difficulty(user_id)

        # Escolha aleatória do tipo de jogo se não especificado
        game_type = game_type if game_type in self.game_types else self._get_appropriate_game_type(
            user_id)

        # Verificação do grupo etário
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

    def update_progress(self, user_id: str, score_increment: int, db_connector=None):
        """
        Atualiza o progresso do usuário em memória e no banco de dados (se disponível)

        Args:
            user_id: ID do usuário
            score_increment: Incremento de pontuação a aplicar
            db_connector: Opcional, instância do DatabaseConnector
        """
        # Atualização em memória
        if user_id in self.current_games:
            # Atualizar dados em memória
            self.current_games[user_id]["score"] += score_increment
            self.current_games[user_id]["current_index"] += 1

            # Obter dados do jogo atual para registrar
            current_game = self.current_games[user_id]

            self.logger.info(
                f"Updated progress for {user_id}: score={current_game['score']}, "
                f"index={current_game['current_index']}, difficulty={current_game['difficulty']}")

            # Salvar no banco de dados se o connector estiver disponível
            if db_connector:
                try:
                    # 1. Obter o usuário atual
                    user = db_connector.get_user(user_id)
                    if not user:
                        self.logger.warning(
                            f"User {user_id} not found in database")
                        return

                    # 2. Atualizar estatísticas do usuário
                    stats = user.get("statistics", {})

                    # Incrementar exercícios completados
                    stats["exercises_completed"] = stats.get(
                        "exercises_completed", 0) + 1

                    # Calcular a precisão com base no score (convertendo para percentual)
                    # Converter para percentual
                    exercise_score = min(100, max(0, score_increment * 10))
                    current_accuracy = stats.get("accuracy", 0)
                    exercises_done = stats.get("exercises_completed", 1)

                    # Média ponderada para atualizar a precisão com suavização
                    new_accuracy = (
                        (current_accuracy * (exercises_done - 1)) + exercise_score) / exercises_done
                    stats["accuracy"] = round(new_accuracy, 2)

                    # 3. Salvar histórico de progresso do jogo atual
                    if "game_progress" not in user:
                        user["game_progress"] = []

                    # Criar registro de progresso
                    progress_entry = {
                        "game_id": current_game.get("game_id"),
                        "timestamp": datetime.datetime.now().isoformat(),
                        "difficulty": current_game.get("difficulty"),
                        "game_type": current_game.get("game_type"),
                        "current_index": current_game.get("current_index"),
                        "total_exercises": len(current_game.get("content", {}).get("exercises", [])),
                        "current_score": current_game.get("score"),
                        "last_exercise_score": score_increment
                    }

                    # Limitar histórico a 10 registros mais recentes, adicionar o novo no início
                    user["game_progress"] = [progress_entry] + \
                        user.get("game_progress", [])[:9]

                    # 4. Atualizar no banco de dados
                    update_data = {
                        "statistics": stats,
                        "game_progress": user["game_progress"]
                    }

                    db_connector.update_user(user_id, update_data)
                    self.logger.info(
                        f"Saved progress to database for user {user_id}: accuracy={stats['accuracy']}, exercises={stats['exercises_completed']}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to save progress to database: {str(e)}")

    def _get_user_difficulty(self, user_id: str) -> str:
        """
        Determina a dificuldade com base no histórico do usuário ou escolhe aleatoriamente.
        25% de chance de escolher aleatoriamente entre os níveis de dificuldade.
        """
        # 25% de chance de escolher uma dificuldade aleatória
        if random.random() < 0.25:
            return random.choice(self.difficulty_levels)

        # Caso contrário, basear na pontuação do usuário
        if user_id in self.current_games:
            score = self.current_games[user_id]["score"]
            if score > 100:
                return "avançado"
            elif score > 50:
                return "médio"
        return "iniciante"

    def _get_appropriate_game_type(self, user_id: str) -> str:
        """
        Escolhe aleatoriamente um tipo de jogo, com preferência para exercícios de pronúncia 
        para usuários novos.
        """
        # Se for um usuário novo, maior probabilidade de começar com exercícios de pronúncia
        if user_id not in self.current_games:
            if random.random() < 0.6:  # 60% de chance
                return "exercícios de pronúncia"

        # Caso contrário, escolha aleatória entre todos os tipos
        return random.choice(self.game_types)

    def _select_target_sound(self, difficulty: str) -> str:
        """
        Seleciona um som-alvo apropriado com base na dificuldade.
        """
        if difficulty == "iniciante":
            # Sons mais simples para iniciantes
            simple_sounds = ["p", "b", "m", "t", "d", "n"]
            return random.choice(simple_sounds)
        elif difficulty == "médio":
            # Sons intermediários
            medium_sounds = ["s", "z", "f", "v", "l", "r"]
            return random.choice(medium_sounds)
        else:  # avançado
            # Sons mais desafiadores
            complex_sounds = ["ch", "j", "lh", "nh", "rr", "x"]
            return random.choice(complex_sounds)

    def _generate_content(self, difficulty: str, game_type: str, age_group: str) -> Dict[str, Any]:
        try:
            if not self.client:
                self.logger.warning(
                    "OpenAI client unavailable. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group)

            system_prompt = self._create_system_prompt(
                game_type, difficulty, age_group)

            # Seleciona um som-alvo apropriado para a dificuldade
            target_sound = self._select_target_sound(difficulty)

            user_prompt = (
                f"Crie um jogo de terapia da fala do tipo '{game_type}' em português para {age_group}, "
                f"nível '{difficulty}', focado no som '{target_sound}'. "
                "Inclua um título criativo, descrição, instruções claras (em lista), 5 exercícios e metadados."
            )

            # Try to use gpt-4o-mini first, which supports response_format parameter
            try:
                self.logger.info(
                    "Attempting to use gpt-4o-mini with JSON response format")
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=500
                )
                content_json = json.loads(response.choices[0].message.content)
            except Exception as e:
                # Fall back to gpt-4o-mini without response_format parameter
                self.logger.info(f"Falling back to gpt-4o-mini: {str(e)}")
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt +
                            " Responda com um objeto JSON."}
                    ],
                    max_tokens=1000
                )
                content_text = response.choices[0].message.content
                try:
                    content_json = json.loads(content_text)
                except json.JSONDecodeError:
                    self.logger.warning(
                        "Failed to parse JSON from gpt-4o-mini response")
                    return self._get_fallback_content(game_type, difficulty, age_group)

            required_keys = ["title", "description",
                             "instructions", "exercises"]
            if not all(key in content_json for key in required_keys):
                self.logger.warning(
                    "Incomplete OpenAI response. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group)

            self.logger.info(
                f"Generated game: {content_json['title']} (Difficulty: {difficulty})")
            return content_json
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return self._get_fallback_content(game_type, difficulty, age_group)

    def _create_system_prompt(self, game_type: str, difficulty: str, age_group: str) -> str:
        # Adicionar instruções específicas para diferentes níveis de dificuldade
        difficulty_guidance = ""
        if difficulty == "iniciante":
            difficulty_guidance = """
# NÍVEL: INICIANTE
- Use palavras simples com 1-2 sílabas
- Foque em sons básicos e fáceis de pronunciar
- Evite combinações de consoantes complexas
- Instruções muito claras e diretas
"""
        elif difficulty == "médio":
            difficulty_guidance = """
# NÍVEL: MÉDIO
- Use palavras com 2-3 sílabas
- Inclua algumas combinações de consoantes moderadas
- Aumenta ligeiramente a complexidade dos exercícios
- Instruções claras mas com desafios adicionais
"""
        else:  # avançado
            difficulty_guidance = """
# NÍVEL: AVANÇADO
- Use palavras mais longas e complexas
- Inclua combinações de consoantes desafiadoras
- Desafie a criança com frases completas quando apropriado
- Aumente a complexidade dos exercícios
"""

        base_prompt = f"""És um especialista em terapia da fala para {age_group} falantes de português.

# CONTEXTO
Estás a criar jogos para uma aplicação de terapia da fala que ajuda {age_group} a melhorar as suas competências de comunicação.
O jogo deve ser adequado para o nível de dificuldade '{difficulty}' e focar no tipo '{game_type}'.

{difficulty_guidance}

# FORMATO DE SAÍDA
Responde com um objeto JSON contendo:
- "title": título criativo do jogo
- "description": breve descrição do objetivo
- "instructions": lista de instruções claras
- "exercises": lista com 5 exercícios específicos
- "target_skills": lista de competências desenvolvidas
- "target_sound": som-alvo do jogo (ex.: "s", "r")
- "estimated_duration": tempo estimado (ex.: "5-10 minutos")
"""

        # Para exercícios de pronúncia, adicionar:
        """
# TIPO: EXERCÍCIOS DE PRONÚNCIA
Cada exercício DEVE ter EXATAMENTE os seguintes campos:
- "word": uma palavra em português para praticar
- "tip": uma dica para ajudar na pronúncia
- "difficulty": nível da palavra de 1-3

Certifica-te que cada exercício tem exatamente esta estrutura sem campos adicionais.
"""
        # For pronunciation exercises, ensure a consistent format
        if game_type == "exercícios de pronúncia":
            return base_prompt + """
# TIPO: EXERCÍCIOS DE PRONÚNCIA
Cada exercício DEVE ter EXATAMENTE os seguintes campos:
- "word": uma palavra em português para praticar
- "tip": uma dica para ajudar na pronúncia
- "difficulty": nível da palavra de 1-3

Certifique-se que cada exercício tenha exatamente esta estrutura sem campos adicionais.
"""
        # Other game types...
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
        elif game_type == "desafios de pronúncia":
            return base_prompt + """
# TIPO: DESAFIOS DE PRONÚNCIA
Cada exercício deve ter: "sentence" (frase), "challenge" (desafio específico).
"""

    def _get_fallback_content(self, game_type: str, difficulty: str, age_group: str) -> Dict[str, Any]:
        """
        Fornece conteúdo de fallback adequado à dificuldade especificada.
        """
        target_sound = self._select_target_sound(difficulty)

        # Exercícios diferenciados por nível de dificuldade
        if difficulty == "iniciante":
            exercises = [
                {"word": "sol", "tip": "Destaque o 's' no início"},
                {"word": "pato", "tip": "Pronuncie o 'p' com os lábios"},
                {"word": "mão", "tip": "Sinta os lábios fechados no 'm'"},
                {"word": "dia", "tip": "Língua toca nos dentes no 'd'"},
                {"word": "vaca", "tip": "Lábios tocam levemente no 'v'"}
            ]
        elif difficulty == "médio":
            exercises = [
                {"word": "sapo", "tip": "Foco no 's' inicial"},
                {"word": "rato", "tip": "Pronuncie o 'r' suavemente"},
                {"word": "lago", "tip": "Destaque o 'l' no início"},
                {"word": "fada", "tip": "Sopre no 'f'"},
                {"word": "zebra", "tip": "Destaque o 'z' inicial"}
            ]
        else:  # avançado
            exercises = [
                {"word": "chocolate", "tip": "Articule o 'ch' claramente"},
                {"word": "gelado", "tip": "Som suave do 'g'"},
                {"word": "carroça", "tip": "Vibre o 'rr' no meio"},
                {"word": "passarinho", "tip": "Destaque o 'nh' no final"},
                {"word": "trabalho", "tip": "Pronuncie o 'lh' corretamente"}
            ]

        if game_type == "exercícios de pronúncia":
            return {
                "title": f"Sons {difficulty.capitalize()}",
                "description": f"Pratique o som-alvo com palavras de nível {difficulty}.",
                "instructions": ["Diga cada palavra em voz alta.", "Tente pronunciar o som destacado corretamente."],
                "exercises": exercises,
                "target_skills": ["articulação", "consciência fonológica"],
                "target_sound": target_sound,
                "estimated_duration": "5-10 minutos"
            }

        # Fallback genérico para outros tipos de jogo
        return {
            "title": f"Jogo de {game_type.capitalize()} - Nível {difficulty.capitalize()}",
            "description": f"Pratique o som '{target_sound}' com atividades de nível {difficulty}.",
            "instructions": ["Siga as instruções para cada exercício.", "Pronuncie claramente."],
            "exercises": exercises,
            "target_skills": ["articulação", "consciência fonológica"],
            "target_sound": target_sound,
            "estimated_duration": "5-10 minutos"
        }

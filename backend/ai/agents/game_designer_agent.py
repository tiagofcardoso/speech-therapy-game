from typing import Optional, Dict, List, Any
import random
import json
import logging
import datetime
from ..server.openai_client import create_openai_client
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class GameDesignerAgent:
    def __init__(self):
        self.client = create_openai_client()
        self.logger = logging.getLogger("GameDesignerAgent")
        self.game_types = ["palavras cruzadas", "adivinhações",
                           "rimas", "exercícios de pronúncia", "desafios de pronúncia",
                           "histórias interativas", "conjunto de imagens", "frases contextuais"]
        self.difficulty_levels = ["iniciante", "médio", "avançado"]
        self.target_sounds = ["s", "r", "l", "p", "t",
                              "ch", "j", "m", "n", "lh", "nh", "rr", "z", "f"]
        self.current_games = {}
        self.user_preferences = {}  # Armazenar preferências de usuário
        self.game_templates = self._load_game_templates()
        self.logger.info("GameDesignerAgent initialized")

    def _load_game_templates(self) -> Dict[str, Any]:
        """Carrega templates de jogos de arquivos JSON se disponíveis ou usa padrões"""
        templates = {}
        template_dir = Path(__file__).parent / "templates"

        # Verificar se o diretório existe, se não, criar
        if not template_dir.exists():
            try:
                template_dir.mkdir(parents=True)
                self.logger.info(
                    f"Criado diretório de templates: {template_dir}")
            except Exception as e:
                self.logger.warning(
                    f"Não foi possível criar diretório de templates: {e}")
                return templates

        # Tenta carregar templates para cada tipo de jogo
        for game_type in self.game_types:
            file_name = game_type.replace(" ", "_") + "_template.json"
            file_path = template_dir / file_name

            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        templates[game_type] = json.load(f)
                    self.logger.info(f"Template carregado: {game_type}")
                except Exception as e:
                    self.logger.warning(
                        f"Erro ao carregar template {file_path}: {e}")

        return templates

    def create_game(self, user_id: str, difficulty: Optional[str] = None, game_type: Optional[str] = None,
                    age_group: Optional[str] = "crianças", db_connector=None) -> Dict[str, Any]:
        self.logger.info(
            f"GameDesignerAgent.create_game called by MCP coordinator for user {user_id}")

        # Considerar preferências do usuário, se disponíveis
        user_prefs = self.user_preferences.get(user_id, {})

        # Se o parâmetro de dificuldade for "aleatório" ou None, escolha baseado no perfil
        if difficulty is None or difficulty == "aleatório":
            difficulty = self._get_user_difficulty(user_id)
        elif difficulty not in self.difficulty_levels:
            difficulty = self._get_user_difficulty(user_id)

        # Escolha tipo de jogo baseado em preferências ou análise de desempenho
        if game_type not in self.game_types:
            game_type = self._get_appropriate_game_type(user_id)

        # Verificação do grupo etário
        age_group = age_group if age_group in [
            "crianças", "adultos"] else "crianças"

        self.logger.info(
            f"Creating game for user {user_id}: difficulty={difficulty}, type={game_type}, age_group={age_group}")

        # Considerar pontos fracos do usuário ao gerar conteúdo
        weak_sounds = user_prefs.get("weak_sounds", [])
        strong_sounds = user_prefs.get("strong_sounds", [])

        # Direcionar o foco para sons fracos se disponível
        target_sound = None
        if weak_sounds and random.random() < 0.7:  # 70% chance de focar em sons fracos
            target_sound = random.choice(weak_sounds)

        # NOVO: Verificar se devemos repetir um jogo anterior com pontuação baixa
        previous_game = self._check_for_game_to_repeat(user_id, db_connector)

        if previous_game:
            self.logger.info(
                f"Repetindo jogo anterior para user {user_id} devido à pontuação baixa")
            game_content = previous_game["content"]
            game_id = previous_game["game_id"]
            difficulty = previous_game["difficulty"]
            game_type = previous_game["game_type"]
        else:
            # Gerar novo conteúdo usando o LLM
            game_content = self._generate_content(
                difficulty, game_type, age_group, target_sound, user_prefs)
            # Gerar um ID de jogo estruturado
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
            game_id = f"game-{timestamp}-{user_id[:5]}"

        # Armazenar o jogo atual com mais metadados
        self.current_games[user_id] = {
            "game_id": game_id,
            "difficulty": difficulty,
            "game_type": game_type,
            "age_group": age_group,
            "content": game_content,
            "current_index": 0,
            "score": 0,
            "created_at": datetime.datetime.now().isoformat(),
            "target_sound": game_content.get("target_sound", "variado"),
            "completed": False,
            "metrics": {
                "accuracy": [],  # Lista para rastrear precisão por exercício
                "time_spent": []  # Lista para rastrear tempo gasto por exercício
            }
        }

        # Estrutura de retorno melhorada
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
                "estimated_duration": game_content.get("estimated_duration", "5-10 minutos"),
                "theme": game_content.get("theme", "geral"),
                "visual_style": game_content.get("visual_style", "padrão"),
                "engagement_level": game_content.get("engagement_level", "médio")
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

    def get_user_progress_summary(self, user_id: str, db_connector=None) -> Dict[str, Any]:
        """
        Obter um resumo do progresso do usuário, combinando dados locais e do banco de dados
        """
        summary = {
            "current_game": None,
            "recent_performance": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_focus": [],
            "total_exercises_completed": 0,
            "average_accuracy": 0
        }

        # Dados do jogo atual em memória
        if user_id in self.current_games:
            current_game = self.current_games[user_id]
            summary["current_game"] = {
                "game_id": current_game.get("game_id"),
                "game_type": current_game.get("game_type"),
                "difficulty": current_game.get("difficulty"),
                "progress": f"{current_game.get('current_index', 0)}/{len(current_game.get('content', {}).get('exercises', []))}",
                "score": current_game.get("score", 0)
            }

        # Dados do banco de dados, se disponível
        if db_connector:
            try:
                user_data = db_connector.get_user(user_id)
                if user_data:
                    # Extrair estatísticas gerais
                    stats = user_data.get("statistics", {})
                    summary["total_exercises_completed"] = stats.get(
                        "exercises_completed", 0)
                    summary["average_accuracy"] = stats.get("accuracy", 0)

                    # Histórico recente de jogos
                    game_progress = user_data.get("game_progress", [])
                    for progress in game_progress[:5]:  # Últimos 5 jogos
                        summary["recent_performance"].append({
                            "game_type": progress.get("game_type"),
                            "difficulty": progress.get("difficulty"),
                            "score": progress.get("current_score"),
                            "completed": progress.get("current_index", 0) >= progress.get("total_exercises", 1),
                            "date": progress.get("timestamp")
                        })

                    # Identificar pontos fortes e fracos
                    if "phoneme_performance" in stats:
                        phonemes = stats["phoneme_performance"]
                        sorted_phonemes = sorted(
                            phonemes.items(), key=lambda x: x[1], reverse=True)

                        # Top 3 pontos fortes
                        summary["strengths"] = [p[0]
                                                for p in sorted_phonemes[:3]]

                        # Bottom 3 pontos fracos
                        summary["weaknesses"] = [p[0]
                                                 for p in sorted_phonemes[-3:]]

                        # Recommended focus (fraquezas + outros sons não praticados recentemente)
                        summary["recommended_focus"] = summary["weaknesses"].copy()

            except Exception as e:
                self.logger.error(
                    f"Erro ao obter dados de progresso: {str(e)}")

        return summary

    def update_progress(self, user_id: str, score_increment: int, db_connector=None,
                        exercise_data: Dict[str, Any] = None):
        """
        Atualiza o progresso do usuário em memória e no banco de dados (se disponível)

        Args:
            user_id: ID do usuário
            score_increment: Incremento de pontuação a aplicar
            db_connector: Opcional, instância do DatabaseConnector
            exercise_data: Dados adicionais sobre o exercício completado
        """
        # Atualização em memória
        if user_id not in self.current_games:
            self.logger.warning(f"User {user_id} has no active game")
            return

        # Obter dados do jogo atual
        current_game = self.current_games[user_id]

        # Atualizar dados em memória
        current_game["score"] += score_increment
        current_game["current_index"] += 1

        # Se exercise_data fornecido, adicionar métricas
        if exercise_data:
            accuracy = exercise_data.get("accuracy", 0)
            time_spent = exercise_data.get("time_spent", 0)
            current_game["metrics"]["accuracy"].append(accuracy)
            current_game["metrics"]["time_spent"].append(time_spent)

            # Atualizar dados do fonema atual
            target_sound = current_game.get("target_sound")
            if target_sound and target_sound not in ["variado", "múltiplo"]:
                # Inicializar preferências do usuário se necessário
                if user_id not in self.user_preferences:
                    self.user_preferences[user_id] = {
                        "weak_sounds": [],
                        "strong_sounds": [],
                        "preferred_games": [],
                        "phoneme_performance": {}
                    }

                # Atualizar desempenho do fonema
                phoneme_perf = self.user_preferences[user_id].get(
                    "phoneme_performance", {})
                if target_sound not in phoneme_perf:
                    phoneme_perf[target_sound] = accuracy
                else:
                    # Média móvel ponderada (70% histórico, 30% atual)
                    phoneme_perf[target_sound] = (
                        phoneme_perf[target_sound] * 0.7) + (accuracy * 0.3)

                # Atualizar classificação de sons fortes/fracos
                self._update_sound_classification(user_id)

        # Verificar se o jogo foi concluído
        total_exercises = len(current_game.get(
            "content", {}).get("exercises", []))
        if current_game["current_index"] >= total_exercises:
            current_game["completed"] = True
            self.logger.info(
                f"Game {current_game['game_id']} completed by user {user_id}")

            # Atualizar preferências: registrar tipo de jogo preferido se pontuação alta
            avg_accuracy = sum(current_game["metrics"]["accuracy"]) / len(
                current_game["metrics"]["accuracy"]) if current_game["metrics"]["accuracy"] else 0
            if avg_accuracy > 0.8:  # Se desempenho foi muito bom
                if user_id in self.user_preferences:
                    game_type = current_game["game_type"]
                    preferred_games = self.user_preferences[user_id].get(
                        "preferred_games", [])
                    if game_type not in preferred_games:
                        preferred_games.append(game_type)
                        # Manter top 5
                        self.user_preferences[user_id]["preferred_games"] = preferred_games[:5]

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

                # Converter para percentual
                exercise_score = min(100, max(0, score_increment * 10))
                current_accuracy = stats.get("accuracy", 0)
                exercises_done = stats.get("exercises_completed", 1)

                # Média ponderada para atualizar a precisão com suavização
                new_accuracy = (
                    (current_accuracy * (exercises_done - 1)) + exercise_score) / exercises_done
                stats["accuracy"] = round(new_accuracy, 2)

                # 3. Atualizar desempenho por fonema, se disponível
                if "phoneme_performance" not in stats:
                    stats["phoneme_performance"] = {}

                target_sound = current_game.get("target_sound")
                if target_sound and target_sound not in ["variado", "múltiplo"] and exercise_data:
                    # Converter para percentual
                    accuracy = exercise_data.get("accuracy", 0) * 100
                    if target_sound not in stats["phoneme_performance"]:
                        stats["phoneme_performance"][target_sound] = accuracy
                    else:
                        # Média móvel
                        current = stats["phoneme_performance"][target_sound]
                        stats["phoneme_performance"][target_sound] = (
                            current * 0.7) + (accuracy * 0.3)

                # 4. Salvar histórico de progresso do jogo atual
                if "game_progress" not in user:
                    user["game_progress"] = []

                # Criar registro de progresso
                progress_entry = {
                    "game_id": current_game.get("game_id"),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "difficulty": current_game.get("difficulty"),
                    "game_type": current_game.get("game_type"),
                    "current_index": current_game.get("current_index"),
                    "total_exercises": total_exercises,
                    "current_score": current_game.get("score"),
                    "last_exercise_score": score_increment,
                    "target_sound": target_sound
                }

                # Limitar histórico a 10 registros mais recentes, adicionar o novo no início
                user["game_progress"] = [progress_entry] + \
                    user.get("game_progress", [])[:9]

                # 5. Atualizar no banco de dados
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

    def _update_sound_classification(self, user_id: str):
        """Atualiza a classificação de sons fortes e fracos com base no desempenho"""
        if user_id not in self.user_preferences:
            return

        phoneme_perf = self.user_preferences[user_id].get(
            "phoneme_performance", {})
        if not phoneme_perf:
            return

        # Ordenar fonemas por desempenho
        sorted_phonemes = sorted(phoneme_perf.items(), key=lambda x: x[1])

        # Bottom 30% são sons fracos, top 30% são sons fortes
        total = len(sorted_phonemes)
        weak_count = max(1, int(total * 0.3))
        strong_count = max(1, int(total * 0.3))

        self.user_preferences[user_id]["weak_sounds"] = [p[0]
                                                         for p in sorted_phonemes[:weak_count]]
        self.user_preferences[user_id]["strong_sounds"] = [
            p[0] for p in sorted_phonemes[-strong_count:]]

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
        Escolhe um tipo de jogo com base nas preferências do usuário ou dados de desempenho
        """
        # Se tivermos preferências registradas, usar com 70% de probabilidade
        if user_id in self.user_preferences:
            preferred_games = self.user_preferences[user_id].get(
                "preferred_games", [])
            if preferred_games and random.random() < 0.7:
                return random.choice(preferred_games)

        # Se for um usuário novo, maior probabilidade de começar com exercícios de pronúncia
        if user_id not in self.current_games:
            if random.random() < 0.6:  # 60% de chance
                return "exercícios de pronúncia"

        # Caso contrário, escolha aleatória entre todos os tipos
        return random.choice(self.game_types)

    def _select_target_sound(self, difficulty: str, weak_sounds=None) -> str:
        """
        Seleciona um som-alvo apropriado com base na dificuldade e fraquezas do usuário.
        """
        # Se temos sons fracos, usar com 70% de probabilidade
        if weak_sounds and random.random() < 0.7:
            return random.choice(weak_sounds)

        # Caso contrário, selecionar com base na dificuldade
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

    def _check_for_game_to_repeat(self, user_id: str, db_connector=None) -> Optional[Dict[str, Any]]:
        """
        Verifica o histórico do usuário para identificar jogos com pontuação baixa (<70) 
        que devem ser repetidos para reforço da aprendizagem.

        Args:
            user_id: ID do usuário
            db_connector: Opcional, instância do DatabaseConnector para acessar histórico completo

        Returns:
            Jogo que deve ser repetido ou None se não houver necessidade de repetição
        """
        self.logger.info(
            f"Analisando histórico para possível repetição de jogo do usuário {user_id}")

        # Jogos recentes com pontuação baixa em memória
        recent_low_score_game = None

        # 1. Verificar histórico recente em memória
        if user_id in self.current_games and self.current_games[user_id].get("completed", False):
            current_game = self.current_games[user_id]
            avg_accuracy = 0

            # Calcular precisão média se disponível
            if current_game["metrics"]["accuracy"]:
                avg_accuracy = sum(
                    current_game["metrics"]["accuracy"]) / len(current_game["metrics"]["accuracy"])

            # Convertendo para escala de 0-100 para comparar com o limiar de 70
            avg_score = avg_accuracy * 100

            if avg_score < 70:
                self.logger.info(
                    f"Encontrado jogo recente com pontuação baixa: {avg_score:.1f}")
                recent_low_score_game = current_game

        # 2. Verificar histórico no banco de dados se disponível e se não encontramos em memória
        if not recent_low_score_game and db_connector:
            try:
                user_data = db_connector.get_user(user_id)
                if user_data and "game_progress" in user_data:
                    # Verificar os três jogos mais recentes
                    for game_record in user_data["game_progress"][:3]:
                        # Converter pontuação para escala comparável
                        score = game_record.get("current_score", 0)
                        if isinstance(score, (int, float)) and score < 70:
                            # Encontrado jogo com pontuação baixa no histórico recente
                            self.logger.info(
                                f"Encontrado jogo com pontuação baixa no histórico: {score}")

                            # Recuperar o jogo completo
                            game_id = game_record.get("game_id")
                            if game_id:
                                # Tentar recuperar o conteúdo completo do jogo
                                game_content = db_connector.get_game(game_id)
                                if game_content:
                                    # Estruturar o jogo para repetição
                                    return {
                                        "game_id": game_id,
                                        "difficulty": game_record.get("difficulty", "médio"),
                                        "game_type": game_record.get("game_type", "exercícios de pronúncia"),
                                        "content": game_content,
                                    }
            except Exception as e:
                self.logger.error(
                    f"Erro ao verificar histórico de jogos: {str(e)}")

        # 3. Determinar se deve repetir o jogo com base na lógica de aprendizagem
        if recent_low_score_game:
            # Probabilidade de repetição baseada na pontuação
            # Quanto menor a pontuação, maior a probabilidade de repetir
            if recent_low_score_game["metrics"]["accuracy"]:
                avg_accuracy = sum(recent_low_score_game["metrics"]["accuracy"]) / len(
                    recent_low_score_game["metrics"]["accuracy"])
                # Ex: 0.6 de precisão = 0.4 de chance de repetir
                repeat_probability = 1.0 - (avg_accuracy)

                if random.random() < repeat_probability:
                    self.logger.info(
                        f"Decidido repetir jogo com pontuação baixa: {avg_accuracy*100:.1f}")
                    return recent_low_score_game
            else:
                # Se não tiver métricas de precisão, mas foi marcado para repetição
                self.logger.info(
                    "Repetindo jogo sem métricas de precisão marcado para repetição")
                return recent_low_score_game

        # Não repetir jogo, gerar novo conteúdo
        self.logger.info(
            "Nenhum jogo identificado para repetição, gerando novo conteúdo")
        return None

    def _generate_content(self, difficulty: str, game_type: str, age_group: str,
                          target_sound=None, user_preferences=None) -> Dict[str, Any]:
        try:
            if not self.client:
                self.logger.warning(
                    "OpenAI client unavailable. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group, target_sound)

            # ALTERADO: Sempre gerar novos jogos usando o LLM, sem usar templates
            system_prompt = self._create_system_prompt(
                game_type, difficulty, age_group, user_preferences)

            # Seleciona um som-alvo apropriado para a dificuldade se não especificado
            if not target_sound:
                weak_sounds = user_preferences.get(
                    "weak_sounds", []) if user_preferences else []
                target_sound = self._select_target_sound(
                    difficulty, weak_sounds)

            user_prompt = (
                f"Crie um jogo de terapia da fala do tipo '{game_type}' em português para {age_group}, "
                f"nível '{difficulty}', focado no som '{target_sound}'. "
                "Inclua um título criativo, descrição, instruções claras (em lista), 5 exercícios e metadados."
            )

            # Try to use gpt-4o-mini first, which supports response_format parameter
            try:
                self.logger.info(
                    "Generating new game content with LLM")
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=1000
                )
                content_json = json.loads(response.choices[0].message.content)
            except Exception as e:
                # Fall back to gpt-4o-mini without response_format parameter
                self.logger.info(
                    f"Falling back to gpt-4o-mini without response_format: {str(e)}")
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt +
                            " Responda com um objeto JSON."}
                    ],
                    max_tokens=1200
                )
                content_text = response.choices[0].message.content
                try:
                    content_json = json.loads(content_text)
                except json.JSONDecodeError:
                    self.logger.warning(
                        "Failed to parse JSON from LLM response")
                    return self._get_fallback_content(game_type, difficulty, age_group, target_sound)

            required_keys = ["title", "description",
                             "instructions", "exercises"]
            if not all(key in content_json for key in required_keys):
                self.logger.warning(
                    "Incomplete LLM response. Using fallback.")
                return self._get_fallback_content(game_type, difficulty, age_group, target_sound)

            # Certificar-se de que o target_sound está no conteúdo retornado
            content_json["target_sound"] = content_json.get(
                "target_sound", target_sound)

            # Adicionar temas e características visuais se não estiverem presentes
            if "theme" not in content_json:
                themes = ["animais", "alimentos", "esportes",
                          "natureza", "viagens", "oceano", "espaço"]
                content_json["theme"] = random.choice(themes)

            if "visual_style" not in content_json:
                styles = ["colorido", "desenho animado",
                          "minimalista", "3D", "aquarela"]
                content_json["visual_style"] = random.choice(styles)

            # ALTERADO: Ainda salvar como template para persistência, mas não para reuso automatizado
            template_available = game_type in self.game_templates
            if not template_available and random.random() < 0.3:  # 30% chance
                self._save_as_template(game_type, content_json)

            self.logger.info(
                f"Generated new game with LLM: {content_json['title']} (Difficulty: {difficulty})")
            return content_json
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return self._get_fallback_content(game_type, difficulty, age_group, target_sound)

    def _create_system_prompt(self, game_type: str, difficulty: str, age_group: str,
                              user_preferences: Dict = None) -> str:
        """
        Cria o prompt de sistema para gerar conteúdo de jogos com o LLM.

        Args:
            game_type: Tipo de jogo a ser criado
            difficulty: Nível de dificuldade (iniciante, médio, avançado)
            age_group: Grupo etário alvo (crianças, adultos)
            user_preferences: Preferências do usuário, se disponíveis

        Returns:
            Texto do prompt de sistema formatado
        """
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

        # Adicionar informações de preferências do usuário, se disponíveis
        user_context = ""
        if user_preferences:
            weak_sounds = user_preferences.get("weak_sounds", [])
            if weak_sounds:
                user_context += f"\n# ÁREAS DE FOCO\nEste usuário precisa praticar especialmente os sons: {', '.join(weak_sounds)}\n"

        base_prompt = f"""És um especialista em terapia da fala para {age_group} falantes de português.

# CONTEXTO
Estás a criar jogos para uma aplicação de terapia da fala que ajuda {age_group} a melhorar as suas competências de comunicação.
O jogo deve ser adequado para o nível de dificuldade '{difficulty}' e focar no tipo '{game_type}'.
{user_context}
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
- "theme": tema visual para o jogo (ex.: "animais", "espaço", "natureza")
- "visual_style": estilo visual sugerido (ex.: "colorido", "desenho animado")
"""

        # Para exercícios de pronúncia, adicionar:
        if game_type == "exercícios de pronúncia":
            return base_prompt + """
# TIPO: EXERCÍCIOS DE PRONÚNCIA
Cada exercício DEVE ter EXATAMENTE os seguintes campos:
- "word": uma palavra em português para praticar
- "tip": uma dica para ajudar na pronúncia
- "difficulty": nível da palavra de 1-3
- "image_hint": breve descrição de imagem relacionada

Certifique-se que cada exercício tenha exatamente esta estrutura sem campos adicionais.
"""
        # Other game types...
        if game_type == "histórias interativas":
            return base_prompt + """
# TIPO: HISTÓRIAS INTERATIVAS
Cada exercício deve ter: 
- "scenario": situação da história
- "target_phrase": frase que a criança deve dizer 
- "context": contexto da situação
- "character": personagem que a criança representa
"""
        elif game_type == "conjunto de imagens":
            return base_prompt + """
# TIPO: CONJUNTO DE IMAGENS
Cada exercício deve ter: 
- "image_description": descrição da imagem a mostrar
- "target_word": palavra que a imagem representa
- "hint": dica para pronunciar corretamente
"""
        elif game_type == "frases contextuais":
            return base_prompt + """
# TIPO: FRASES CONTEXTUAIS
Cada exercício deve ter: 
- "situation": descrição da situação
- "phrase": frase completa para praticar
- "target_sounds": sons específicos a praticar na frase
"""
        elif game_type == "palavras cruzadas":
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

        # Padrão para outros tipos de jogos
        return base_prompt

    def _get_fallback_content(self, game_type: str, difficulty: str, age_group: str, target_sound: str = None) -> Dict[str, Any]:
        """
        Gera conteúdo de fallback quando a chamada ao LLM falha.
        Cria um jogo simples baseado no tipo e dificuldade solicitados.

        Args:
            game_type: Tipo de jogo a ser criado
            difficulty: Nível de dificuldade
            age_group: Grupo etário (crianças, adultos)
            target_sound: Som alvo opcional

        Returns:
            Dicionário com o conteúdo do jogo de fallback
        """
        self.logger.info(
            f"Gerando conteúdo de fallback para {game_type}, dificuldade {difficulty}")

        # Definir som alvo padrão se não for fornecido
        if not target_sound:
            if difficulty == "iniciante":
                target_sound = random.choice(["p", "b", "m", "t", "d", "n"])
            elif difficulty == "médio":
                target_sound = random.choice(["s", "z", "f", "v", "l", "r"])
            else:
                target_sound = random.choice(
                    ["ch", "j", "lh", "nh", "rr", "x"])

        # Palavras para cada som (simplificadas para fallback)
        sound_words = {
            "p": ["pato", "pé", "pipoca", "porta", "pula"],
            "b": ["bola", "boca", "bebê", "barco", "banana"],
            "m": ["mão", "mesa", "meia", "mamãe", "maçã"],
            "t": ["tatu", "tomada", "telhado", "tapete", "telefone"],
            "d": ["dado", "dedo", "dia", "doce", "dois"],
            "n": ["nariz", "navio", "ninho", "nome", "nuvem"],
            "s": ["sapo", "sino", "sol", "sopa", "sapato"],
            "z": ["zebra", "zero", "zigzag", "zoológico", "zinco"],
            "f": ["faca", "fogo", "foto", "feijão", "festa"],
            "v": ["vaca", "vovó", "vida", "vale", "vela"],
            "l": ["lua", "lata", "lobo", "livro", "lápis"],
            "r": ["rato", "rua", "rosa", "rei", "roupa"],
            "ch": ["chuva", "chave", "chá", "chinelo", "chocolate"],
            "j": ["janela", "jogo", "jeito", "jabuti", "joia"],
            "lh": ["palha", "palheta", "coelho", "milho", "toalha"],
            "nh": ["ninho", "sonho", "banho", "linha", "marinheiro"],
            "rr": ["carro", "terra", "ferro", "serra", "erro"],
            "x": ["xícara", "xadrez", "xerox", "peixe", "caixa"]
        }

        # Palavras padrão se o som não estiver na lista
        default_words = ["casa", "mundo", "carinho", "pessoa", "felicidade"]

        # Obter palavras para o som alvo ou usar padrão
        words = sound_words.get(target_sound, default_words)

        # Título e descrição padrão baseados no tipo de jogo
        if game_type == "exercícios de pronúncia":
            title = f"Exercícios com o Som {target_sound.upper()}"
            description = f"Praticar a pronúncia do som '{target_sound}' com palavras divertidas."

            # Criar exercícios para este tipo
            exercises = []
            for i, word in enumerate(words):
                exercises.append({
                    "word": word,
                    "tip": f"Respire fundo e concentre-se no som '{target_sound}'",
                    "difficulty": 1 if difficulty == "iniciante" else (2 if difficulty == "médio" else 3),
                    "image_hint": f"Imagem de {word}"
                })

        elif game_type == "histórias interativas":
            title = f"História com o Som {target_sound.upper()}"
            description = f"Uma história divertida para praticar o som '{target_sound}'."

            # Criar exercícios para este tipo
            exercises = []
            scenarios = ["no parque", "na escola",
                         "em casa", "no zoológico", "na praia"]
            for i, word in enumerate(words):
                exercises.append({
                    "scenario": f"Você está {scenarios[i]}",
                    "target_phrase": f"Eu vejo um {word}!",
                    "context": f"Você precisa dizer o que vê",
                    "character": "explorador"
                })

        elif game_type == "conjunto de imagens":
            title = f"Imagens com o Som {target_sound.upper()}"
            description = f"Identificar e pronunciar palavras com o som '{target_sound}'."

            # Criar exercícios para este tipo
            exercises = []
            for word in words:
                exercises.append({
                    "image_description": f"Imagem clara de {word}",
                    "target_word": word,
                    "hint": f"Esta palavra tem o som '{target_sound}'"
                })

        else:  # Tipo genérico para outros jogos
            title = f"Jogando com o Som {target_sound.upper()}"
            description = f"Atividades para praticar o som '{target_sound}'."

            # Criar exercícios genéricos
            exercises = []
            for word in words:
                exercises.append({
                    "target_text": word,
                    "instruction": f"Diga a palavra '{word}' claramente",
                    "tip": f"Foque no som '{target_sound}'"
                })

        # Criar conteúdo de fallback completo
        fallback_content = {
            "title": title,
            "description": description,
            "instructions": [
                f"Pratique o som '{target_sound}' com atenção",
                "Respire fundo antes de cada tentativa",
                "Tente acompanhar as dicas fornecidas"
            ],
            "exercises": exercises,
            "target_sound": target_sound,
            "target_skills": ["pronúncia", "articulação", "consciência fonológica"],
            "estimated_duration": "5-10 minutos",
            "theme": "aprendizado",
            "visual_style": "colorido"
        }

        self.logger.info(
            f"Conteúdo de fallback gerado com sucesso para o som '{target_sound}'")
        return fallback_content

    def _save_as_template(self, game_type: str, content: Dict[str, Any]) -> bool:
        """
        Salva um jogo gerado como template para uso futuro.

        Args:
            game_type: Tipo de jogo para salvar
            content: Conteúdo do jogo a ser salvo como template

        Returns:
            True se o template foi salvo com sucesso, False caso contrário
        """
        try:
            template_dir = Path(__file__).parent / "templates"

            # Certificar que o diretório existe
            if not template_dir.exists():
                template_dir.mkdir(parents=True)
                self.logger.info(
                    f"Criado diretório de templates: {template_dir}")

            # Criar nome de arquivo para o template
            file_name = game_type.replace(" ", "_") + "_template.json"
            file_path = template_dir / file_name

            # Salvar o conteúdo no arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Template salvo para {game_type}: {file_path}")

            # Atualizar o dicionário de templates em memória
            self.game_templates[game_type] = content

            return True

        except Exception as e:
            self.logger.error(
                f"Erro ao salvar template para {game_type}: {str(e)}")
            return False

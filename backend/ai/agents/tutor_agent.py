from typing import Dict, Any, Optional, List
import json
import logging
import os
import random
import datetime
from openai import OpenAI
from speech.synthesis import synthesize_speech

# Configuração adequada do logging
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

    def create_instructions(self, user_profile: Dict[str, Any], difficulty: str) -> Dict[str, Any]:
        """Cria instruções personalizadas para o usuário com base no perfil"""
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
                response = self.client.chat.completions.create(
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
                response = self.client.chat.completions.create(
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

                    greeting_audio = synthesize_speech(
                        instructions["greeting"], voice_settings)
                    explanation_audio = synthesize_speech(
                        instructions["explanation"], voice_settings)
                    encouragement_audio = synthesize_speech(
                        instructions["encouragement"], voice_settings)

                    # Sintetizar dicas opcionais
                    tips_audio = None
                    if "tips" in instructions and isinstance(instructions["tips"], list) and instructions["tips"]:
                        tips_text = ". ".join(instructions["tips"])
                        tips_audio = synthesize_speech(
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
                        "greeting": synthesize_speech(default_instructions["greeting"], voice_settings),
                        "explanation": synthesize_speech(default_instructions["explanation"], voice_settings),
                        "encouragement": synthesize_speech(default_instructions["encouragement"], voice_settings)
                    }
                except Exception as e:
                    self.logger.error(
                        f"Falha ao gerar voz para instruções padrão: {str(e)}")

            return default_instructions

    def provide_feedback(self, user_id: str, response: str, speech_evaluation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fornece feedback personalizado com base na resposta do usuário e na avaliação de fala

        Args:
            user_id: ID do usuário
            response: Texto reconhecido do usuário
            speech_evaluation: Avaliação detalhada da fala pelo SpeechEvaluatorAgent (opcional)

        Returns:
            Feedback com score, mensagem, indicação de acerto, etc.
        """
        self.logger.info(
            f"TutorAgent.provide_feedback chamado para usuário {user_id}")

        # Verificar se há jogo ativo
        current_exercise = self.game_designer.get_current_exercise(user_id)
        if not current_exercise:
            self.logger.warning(f"Nenhum jogo ativo para usuário {user_id}")
            error_message = "Nenhum jogo ativo encontrado para este utilizador"
            return {
                "error": error_message,
                "message": error_message,
                "audio": synthesize_speech(error_message) if self.voice_enabled else None
            }

        # Obter dados do jogo atual
        game_type = self.game_designer.current_games[user_id]["game_type"]
        expected = self._get_expected_word(current_exercise, game_type)

        # Usar avaliação do SpeechEvaluatorAgent, se disponível
        if speech_evaluation:
            score = int(speech_evaluation.get("accuracy", 0)
                        * 10)  # Converter de 0-1 para 0-10
            explanation = speech_evaluation.get("details", {}).get(
                "phonetic_analysis", "Avaliação baseada na precisão")
            strengths = speech_evaluation.get("strengths", [])
            areas_to_improve = speech_evaluation.get("improvement_areas", [])
        else:
            # Caso contrário, fazer avaliação própria
            evaluation = self._evaluate_pronunciation(response, expected)
            score = evaluation.get("score", 5)
            explanation = evaluation.get("explanation", "Avaliação padrão")
            strengths = []
            areas_to_improve = []

        # Selecionar uma persona para este feedback
        persona = self._select_persona_for_user(user_id)

        # Gerar feedback personalizado baseado no score e na persona
        feedback_text = self._generate_personalized_feedback(
            score,
            explanation,
            expected,
            response,
            user_id,
            persona,
            strengths,
            areas_to_improve
        )

        # Atualizar o progresso do usuário
        self._update_user_progress(user_id, score, response, expected)

        # Estrutura completa de feedback
        feedback = {
            "score": score,
            "message": feedback_text,
            "correct": score >= 7,
            "next_exercise": self.game_designer.get_current_exercise(user_id) is not None,
            "performance_details": {
                "expected": expected,
                "actual": response,
                "strengths": strengths,
                "areas_to_improve": areas_to_improve
            },
            "encouragement": random.choice(persona["encouragements"])
        }

        # Adicionar áudio se voz estiver habilitada
        if self.voice_enabled:
            try:
                voice_settings = self.voice_settings.get(persona["voice"],
                                                         {"voice_id": "Ines", "engine": "neural"})
                feedback["audio"] = synthesize_speech(
                    feedback_text, voice_settings)
                feedback["audio_encouragement"] = synthesize_speech(
                    feedback["encouragement"], voice_settings)
            except Exception as e:
                self.logger.error(f"Erro gerando feedback de voz: {str(e)}")

        return feedback

    def _get_expected_word(self, exercise: Dict[str, Any], game_type: str) -> str:
        """Extrai a palavra ou frase esperada com base no tipo de jogo e exercício"""
        if game_type == "palavras cruzadas":
            return exercise.get("word", "sol")
        elif game_type == "adivinhações":
            return exercise.get("answer", "sol")
        elif game_type == "rimas":
            return exercise.get("starter", "sol")
        elif game_type == "exercícios de pronúncia":
            return exercise.get("word", "sol")
        elif game_type == "desafios de pronúncia":
            return exercise.get("sentence", "sol")
        elif game_type == "histórias interativas":
            return exercise.get("target_phrase", "sol")
        elif game_type == "conjunto de imagens":
            return exercise.get("target_word", "sol")
        elif game_type == "frases contextuais":
            return exercise.get("phrase", "sol")
        return "sol"  # Padrão para outros tipos

    def _evaluate_pronunciation(self, actual: str, expected: str) -> Dict[str, Any]:
        """Avalia a pronúncia comparando o texto falado com o esperado"""
        try:
            # Tentar com gpt-4o-mini que suporta formato de resposta JSON
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "És um assistente de terapia da fala especializado em avaliação de pronúncia em português."},
                        {"role": "user", "content": (
                            f"Texto esperado: '{expected}'. Texto reconhecido do utilizador: '{actual}'. "
                            "Retorna um JSON com 'score' (1-10), 'explanation' (explicação detalhada), 'strengths' (lista de pontos fortes) e 'areas_to_improve' (lista de áreas a melhorar)."
                        )}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=200
                )
                evaluation = json.loads(response.choices[0].message.content)
            except Exception as e:
                self.logger.error(f"Erro com gpt-4o-mini: {str(e)}")
                # Fallback para gpt-4o-mini sem response_format
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "És um assistente de terapia da fala especializado em avaliação de pronúncia em português."},
                        {"role": "user", "content": (
                            f"Texto esperado: '{expected}'. Texto reconhecido do utilizador: '{actual}'. "
                            "Retorne um JSON com 'score' (1-10), 'explanation' (explicação detalhada). IMPORTANTE: responda somente o objeto JSON."
                        )}
                    ],
                    max_tokens=200
                )
                try:
                    evaluation = json.loads(
                        response.choices[0].message.content)
                except json.JSONDecodeError:
                    self.logger.warning("Falha ao analisar resposta JSON")
                    return {"score": 5, "explanation": "Avaliação padrão devido a erro no processamento"}

            self.logger.info(
                f"Avaliação de pronúncia para '{expected}': {evaluation}")
            return evaluation
        except Exception as e:
            self.logger.error(f"Erro ao avaliar pronúncia: {str(e)}")
            return {"score": 5, "explanation": "Não foi possível avaliar a pronúncia"}

    def _generate_personalized_feedback(self, score: int, explanation: str, expected: str,
                                        actual: str, user_id: str, persona: Dict,
                                        strengths: List = None, areas_to_improve: List = None) -> str:
        """
        Gera feedback personalizado com base nos resultados da avaliação e na persona do tutor
        """
        try:
            # Obter histórico de tentativas recentes para este usuário (se disponível)
            recent_attempts = []
            if user_id in self.user_sessions:
                recent_attempts = self.user_sessions[user_id].get(
                    "recent_attempts", [])

            # Determinar se o usuário tem melhorado, piorado ou mantido constante
            trend = "constante"
            if len(recent_attempts) >= 3:
                recent_scores = [a.get("score", 0)
                                 for a in recent_attempts[-3:]]
                if all(recent_scores[i] < recent_scores[i+1] for i in range(len(recent_scores)-1)):
                    trend = "melhorando"
                elif all(recent_scores[i] > recent_scores[i+1] for i in range(len(recent_scores)-1)):
                    trend = "piorando"

            # Contexto para personalização do feedback
            consistency = "primeira tentativa"
            if len(recent_attempts) > 0:
                consistency = "inconsistente" if len(
                    set(a.get("score", 0) for a in recent_attempts[-3:])) > 1 else "consistente"

            # Áreas a melhorar e pontos fortes
            strengths_text = ", ".join(strengths) if strengths else ""
            areas_to_improve_text = ", ".join(
                areas_to_improve) if areas_to_improve else ""

            # Construir o prompt para feedback
            prompt = f"""
            Cria feedback encorajador e personalizado para alguém que tentou dizer '{expected}' e o sistema reconheceu '{actual}'.
            
            Contexto adicional:
            - Estilo do tutor: {persona['style']}
            - Pontuação: {score}/10
            - Avaliação técnica: {explanation}
            - Tendência recente: {trend}
            - Consistência: {consistency}
            - Pontos fortes: {strengths_text}
            - Áreas para melhorar: {areas_to_improve_text}
            
            Usa português europeu (de Portugal, não do Brasil).
            Inclui dicas específicas baseadas nas áreas que precisam de melhoria.
            Se a pontuação for alta (8+), seja muito positivo. Se for baixa (<5), seja encorajador mas honesto.
            Seja conciso (máximo 3 frases).
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                        "content": f"És um terapeuta da fala {persona['style']} que trabalha com crianças."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )

            feedback = response.choices[0].message.content.strip()

            # Adicionar emoji da persona para personalização
            if not feedback.endswith(("!", ".", "?")):
                feedback += "."

            feedback += f" {persona['emoji']}"

            return feedback

        except Exception as e:
            self.logger.error(f"Erro gerando feedback personalizado: {str(e)}")
            return f"Boa tentativa com '{expected}'! {persona['emoji']} Vamos continuar praticando."

    def _update_user_progress(self, user_id: str, score: int, response: str, expected: str):
        """
        Atualiza o progresso do usuário e mantém um histórico de tentativas para análise
        """
        # Inicializar dados da sessão do usuário se necessário
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "attempts": 0,
                "total_score": 0,
                "recent_attempts": [],
                "session_start": datetime.datetime.now().isoformat()
            }

        session = self.user_sessions[user_id]

        # Atualizar contadores
        session["attempts"] += 1
        session["total_score"] += score

        # Registrar esta tentativa no histórico recente (manter máx. 10)
        attempt = {
            "timestamp": datetime.datetime.now().isoformat(),
            "expected": expected,
            "actual": response,
            "score": score
        }

        # Manter histórico limitado para não ocupar muita memória
        if "recent_attempts" not in session:
            session["recent_attempts"] = []

        session["recent_attempts"].append(attempt)
        if len(session["recent_attempts"]) > 10:
            session["recent_attempts"].pop(0)

        # Atualizar progresso no GameDesigner
        self.game_designer.update_progress(user_id, score)

        self.logger.info(
            f"Progresso atualizado para {user_id}: tentativas={session['attempts']}, "
            f"pontuação_total={session['total_score']}, score_médio={session['total_score']/session['attempts']:.1f}")

    def _select_persona_for_user(self, user_id: str, age: int = None) -> Dict:
        """
        Seleciona uma persona de tutor apropriada para o usuário
        com base em preferências armazenadas ou idade
        """
        # Se já temos uma persona armazenada para este usuário, mantê-la para consistência
        if user_id in self.user_sessions and "persona" in self.user_sessions[user_id]:
            persona_key = self.user_sessions[user_id]["persona"]
            if persona_key in self.tutor_personas:
                return self.tutor_personas[persona_key]

        # Para crianças mais novas, preferir persona animada
        if age is not None:
            if age < 7:
                persona_key = "animado"
            elif age < 12:
                persona_key = random.choice(["animado", "engraçado"])
            else:
                persona_key = random.choice(["calmo", "engraçado"])
        else:
            # Se não temos idade, escolher aleatoriamente
            persona_key = random.choice(list(self.tutor_personas.keys()))

        # Armazenar a escolha para uso futuro
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["persona"] = persona_key
        else:
            self.user_sessions[user_id] = {"persona": persona_key}

        return self.tutor_personas[persona_key]

    def _record_session_start(self, user_id: str, difficulty: str):
        """
        Registra o início de uma nova sessão para análise de longo prazo
        """
        # Inicializar histórico de interação se não existir
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = {"sessions": []}

        # Obter informações do jogo atual, se disponível
        game_type = "desconhecido"
        target_sound = "desconhecido"

        if user_id in self.game_designer.current_games:
            current_game = self.game_designer.current_games[user_id]
            game_type = current_game.get("game_type", "desconhecido")
            target_sound = current_game.get("target_sound", "desconhecido")

        # Registrar nova sessão
        session = {
            "date": datetime.datetime.now().isoformat(),
            "difficulty": difficulty,
            "game_type": game_type,
            "target_sound": target_sound,
            "performance": "pendente",  # Será atualizado no final da sessão
            "complete": False
        }

        self.interaction_history[user_id]["sessions"].append(session)

        # Limitar histórico a 20 sessões
        if len(self.interaction_history[user_id]["sessions"]) > 20:
            self.interaction_history[user_id]["sessions"].pop(0)

    def complete_session(self, user_id: str):
        """
        Finaliza a sessão atual e atualiza o histórico com os resultados
        """
        if user_id not in self.interaction_history:
            return

        sessions = self.interaction_history[user_id]["sessions"]
        if not sessions:
            return

        # Obter a sessão atual (mais recente)
        current_session = sessions[-1]

        # Calcular desempenho médio se tivermos dados de sessão
        performance = "N/A"
        if user_id in self.user_sessions:
            session_data = self.user_sessions[user_id]
            if session_data["attempts"] > 0:
                avg_score = session_data["total_score"] / \
                    session_data["attempts"]
                if avg_score >= 8:
                    performance = "excelente"
                elif avg_score >= 6:
                    performance = "bom"
                elif avg_score >= 4:
                    performance = "regular"
                else:
                    performance = "precisa melhorar"

        # Atualizar os dados da sessão
        current_session["performance"] = performance
        current_session["complete"] = True
        current_session["attempts"] = self.user_sessions[user_id]["attempts"] if user_id in self.user_sessions else 0

        self.logger.info(
            f"Sessão completa para usuário {user_id}: performance={performance}")

        # Limpar dados da sessão atual
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = {
                "persona": self.user_sessions[user_id].get("persona", "animado")
            }

    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna um resumo do progresso do usuário ao longo do tempo
        """
        progress = {
            "recent_sessions": [],
            "overall_performance": "N/A",
            "improvement_trend": "estável",
            "challenges": [],
            "strengths": []
        }

        # Obter histórico de sessões
        if user_id in self.interaction_history:
            sessions = self.interaction_history[user_id]["sessions"]
            completed_sessions = [s for s in sessions if s["complete"]]

            if completed_sessions:
                # Adicionar sessões recentes
                # últimas 5 sessões
                progress["recent_sessions"] = completed_sessions[-5:]

                # Avaliar desempenho geral
                performances = [s["performance"] for s in completed_sessions]
                if performances:
                    perf_map = {"excelente": 4, "bom": 3,
                                "regular": 2, "precisa melhorar": 1, "N/A": 0}
                    avg_perf = sum(perf_map.get(p, 0)
                                   for p in performances) / len(performances)

                    if avg_perf >= 3.5:
                        progress["overall_performance"] = "excelente"
                    elif avg_perf >= 2.5:
                        progress["overall_performance"] = "bom"
                    elif avg_perf >= 1.5:
                        progress["overall_performance"] = "regular"
                    else:
                        progress["overall_performance"] = "precisa melhorar"

                # Analisar tendência de melhoria
                if len(completed_sessions) >= 3:
                    recent_perfs = [perf_map.get(
                        s["performance"], 0) for s in completed_sessions[-3:]]
                    if all(recent_perfs[i] < recent_perfs[i+1] for i in range(len(recent_perfs)-1)):
                        progress["improvement_trend"] = "melhorando"
                    elif all(recent_perfs[i] > recent_perfs[i+1] for i in range(len(recent_perfs)-1)):
                        progress["improvement_trend"] = "piorando"

        return progress

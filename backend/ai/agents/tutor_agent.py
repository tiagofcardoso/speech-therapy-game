from typing import Dict, List, Any, Optional
import logging
import os
import random
import datetime
import json
from openai import OpenAI
from ai.server.openai_client import create_openai_client
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
        self.search_api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")

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

        # Registrar ferramentas do tutor
        self.tool_registry = {
            'search_internet': self._search_internet,
            'create_instructions': self.create_instructions,
            'provide_feedback': self.provide_feedback,
            'evaluate_response': self.evaluate_response
        }

        self.logger.info(
            f"TutorAgent inicializado com voz {'ativada' if self.voice_enabled else 'desativada'}")

    def _search_internet(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Realiza uma pesquisa na internet usando a API do Google Search

        Args:
            query: Texto a ser pesquisado
            max_results: Número máximo de resultados (padrão: 3)

        Returns:
            Dicionário com resultados da pesquisa
        """
        try:
            if not self.search_api_key or not self.search_engine_id:
                self.logger.warning(
                    "Chaves da API de pesquisa não configuradas")
                return {"error": "API de pesquisa não configurada", "results": []}

            import requests
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.search_api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': max_results
            }

            response = requests.get(url, params=params)
            if response.status_code != 200:
                self.logger.error(f"Erro na pesquisa: {response.status_code}")
                return {"error": f"Erro na API: {response.status_code}", "results": []}

            data = response.json()
            results = []

            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    })

            self.logger.info(
                f"Pesquisa realizada com sucesso: {len(results)} resultados")
            return {
                "success": True,
                "results": results
            }

        except Exception as e:
            self.logger.error(f"Erro ao realizar pesquisa: {str(e)}")
            return {"error": str(e), "results": []}

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
                        f"Erro ao gerar áudio para instruções: {str(e)}")

            return instructions

        except Exception as e:
            self.logger.error(f"Erro ao criar instruções: {str(e)}")
            return {
                "error": str(e),
                "greeting": f"Olá, {name}!",
                "explanation": "Desculpa, estou com algumas dificuldades técnicas.",
                "encouragement": "Vamos tentar mesmo assim!"
            }

    def provide_feedback(self, user_id: str, response: str, speech_evaluation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fornece feedback personalizado com base na resposta do usuário e avaliação de fala
        """
        if user_id not in self.game_designer.current_games:
            self.logger.error(f"Nenhum jogo ativo para usuário {user_id}")
            error_message = "Por favor, inicie um novo jogo para receber feedback."
            return {
                "score": 0,
                "message": error_message,
                "audio": synthesize_speech(error_message) if self.voice_enabled else None
            }

        # Obter dados do jogo atual
        game_type = self.game_designer.current_games[user_id]["game_type"]
        current_exercise = self.game_designer.get_current_exercise(user_id)
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
                from speech.synthesis import synthesize_speech
                feedback["audio"] = synthesize_speech(
                    feedback_text, voice_settings)
                feedback["audio_encouragement"] = synthesize_speech(
                    feedback["encouragement"], voice_settings)
            except Exception as e:
                self.logger.error(f"Erro gerando feedback de voz: {str(e)}")

        return feedback

    def evaluate_response(self, user_id: str, response: str, expected: str, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia a resposta do usuário e fornece feedback personalizado
        """
        # Obter avaliação detalhada
        evaluation = self._evaluate_pronunciation(response, expected)
        score = evaluation.get("score", 5)
        explanation = evaluation.get("explanation", "Avaliação padrão")

        # Selecionar persona apropriada
        persona = self._select_persona_for_user(user_id)

        # Gerar feedback personalizado
        feedback = self._generate_personalized_feedback(
            score, explanation, expected, response, user_id, persona)

        # Atualizar progresso do usuário
        self._update_user_progress(user_id, score, response, expected)

        evaluation["feedback"] = feedback

        return evaluation

    def _select_persona_for_user(self, user_id: str, age: int = None) -> Dict:
        """
        Seleciona uma persona apropriada para o usuário com base na idade e histórico
        """
        # Se temos uma persona já escolhida para esta sessão, manter consistência
        if user_id in self.user_sessions and "persona" in self.user_sessions[user_id]:
            persona_key = self.user_sessions[user_id]["persona"]
            return self.tutor_personas[persona_key]

        if age:
            # Escolher persona baseada na idade
            if age < 7:
                # Mais engraçado/animado para crianças pequenas
                persona_key = random.choice(["animado", "engraçado"])
            elif age < 12:
                # Mix de todas as personas para idade intermediária
                persona_key = random.choice(list(self.tutor_personas.keys()))
            else:
                # Mais calmo/focado para adolescentes e adultos
                persona_key = "calmo"
        else:
            # Se não temos idade, escolher aleatoriamente
            persona_key = random.choice(list(self.tutor_personas.keys()))

        # Armazenar a escolha para uso futuro
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["persona"] = persona_key
        else:
            self.user_sessions[user_id] = {"persona": persona_key}

        return self.tutor_personas[persona_key]

    def _generate_personalized_feedback(self, score: int, explanation: str, expected: str,
                                        actual: str, user_id: str, persona: Dict,
                                        strengths: List = None, areas_to_improve: List = None) -> str:
        """
        Gera feedback personalizado com base nos resultados da avaliação e na persona do tutor
        """
        if score >= 9:
            return f"Uau! {persona['emoji']} Excelente pronúncia de '{expected}'! {random.choice(persona['encouragements'])}"
        elif score >= 7:
            return f"Muito bem! {persona['emoji']} Boa pronúncia de '{expected}'. {random.choice(persona['encouragements'])}"
        elif score >= 5:
            tips = []
            if areas_to_improve:
                tips.extend(
                    [f"Foca mais no som '{s}'" for s in areas_to_improve[:2]])
            tips.append("Tenta falar mais devagar")
            tip = random.choice(tips)
            return f"Quase lá! {persona['emoji']} {tip} em '{expected}'. Vamos tentar novamente!"
        else:
            return f"Boa tentativa com '{expected}'! {persona['emoji']} Vamos continuar praticando."

    def _evaluate_pronunciation(self, actual: str, expected: str) -> Dict[str, Any]:
        """
        Avalia a pronúncia comparando o texto falado com o esperado
        Retorna score (0-10) e explicação
        """
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, actual.lower(),
                                     expected.lower()).ratio()
        score = int(similarity * 10)

        if score >= 9:
            explanation = "Pronúncia perfeita!"
        elif score >= 7:
            explanation = "Boa pronúncia, pequenos ajustes necessários."
        elif score >= 5:
            explanation = "Pronúncia OK, mas precisa melhorar alguns sons."
        else:
            explanation = "Vamos praticar mais este som."

        return {
            "score": score,
            "explanation": explanation,
            "similarity": similarity
        }

    def _get_expected_word(self, exercise: Dict[str, Any], game_type: str) -> str:
        """Extrai a palavra ou frase esperada com base no tipo de jogo e exercício"""
        if not exercise:
            return ""

        if game_type == "exercícios de pronúncia":
            return exercise.get("word", "")
        elif game_type == "histórias interativas":
            return exercise.get("target_phrase", "")
        elif game_type == "conjunto de imagens":
            return exercise.get("target_word", "")
        elif game_type == "frases contextuais":
            return exercise.get("phrase", "")
        else:
            return exercise.get("target_text", "")

    def _update_user_progress(self, user_id: str, score: int, response: str, expected: str):
        """Atualiza o histórico de interações do usuário"""
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = {"sessions": []}

        session = self.interaction_history[user_id]["sessions"][-1] if self.interaction_history[user_id]["sessions"] else None

        if session and not session.get("complete", False):
            # Atualizar sessão existente
            session["responses"].append({
                "expected": expected,
                "actual": response,
                "score": score,
                "timestamp": datetime.datetime.now().isoformat()
            })

            # Calcular performance média da sessão
            scores = [r["score"] for r in session["responses"]]
            avg_score = sum(scores) / len(scores)
            if avg_score >= 8:
                session["performance"] = "excelente"
            elif avg_score >= 6:
                session["performance"] = "bom"
            else:
                session["performance"] = "precisa praticar mais"
        else:
            # Iniciar nova sessão
            self.interaction_history[user_id]["sessions"].append({
                "date": datetime.datetime.now().isoformat(),
                "game_type": self.game_designer.current_games[user_id]["game_type"],
                "target_sound": self.game_designer.current_games[user_id].get("target_sound", "variado"),
                "responses": [{
                    "expected": expected,
                    "actual": response,
                    "score": score,
                    "timestamp": datetime.datetime.now().isoformat()
                }],
                "performance": "em andamento",
                "complete": False
            })

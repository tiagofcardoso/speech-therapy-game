from typing import Dict, Any, List, Optional, Union
import logging
import json
from openai import OpenAI
from .search_tool import GoogleSearchTool

logger = logging.getLogger("AITools")


class AITools:
    """
    Classe centralizada para gerenciar as ferramentas de IA utilizadas pelos agentes
    """

    def __init__(self, client: OpenAI):
        """
        Inicializa as ferramentas de IA com um cliente OpenAI

        Args:
            client: Cliente OpenAI inicializado
        """
        self.client = client
        self.logger = logging.getLogger("AITools")

        # Inicializar a ferramenta de busca Google
        try:
            self.search_tool = GoogleSearchTool()
            self.search_enabled = True
            self.logger.info(
                "Ferramenta de busca Google inicializada com sucesso")
        except Exception as e:
            self.search_enabled = False
            self.logger.warning(
                f"Erro ao inicializar ferramenta de busca Google: {str(e)}")

        self.logger.info("AI Tools initialized")

    def generate_text(self,
                      system_prompt: str,
                      user_prompt: str,
                      model: str = "gpt-4o-mini",
                      temperature: float = 0.7,
                      max_tokens: int = 1000) -> str:
        """
        Gera texto usando o modelo de IA
        """
        try:
            self.logger.info(f"Generating text with {model}")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"

    def generate_json(self,
                      system_prompt: str,
                      user_prompt: str,
                      model: str = "gpt-4o-mini",
                      temperature: float = 0.7,
                      max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Gera uma resposta em formato JSON usando o modelo de IA
        """
        try:
            self.logger.info(f"Generating JSON with {model}")

            # Tentar usar response_format para JSON
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return json.loads(response.choices[0].message.content)
            except Exception as format_error:
                # Fallback: usar prompt para gerar JSON
                self.logger.info(
                    f"Falling back to structured prompt for JSON: {str(format_error)}")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"{system_prompt}\nResponda usando um objeto JSON válido."},
                        {"role": "user",
                            "content": f"{user_prompt}\nResponda com um objeto JSON."}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Tentar analisar o JSON da resposta
                content = response.choices[0].message.content
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Se falhar, tentar extrair JSON de um bloco de código
                    if "```json" in content and "```" in content.split("```json", 1)[1]:
                        json_text = content.split("```json", 1)[
                            1].split("```", 1)[0]
                        return json.loads(json_text)
                    elif "```" in content and "```" in content.split("```", 1)[1]:
                        json_text = content.split(
                            "```", 1)[1].split("```", 1)[0]
                        return json.loads(json_text)
                    else:
                        self.logger.error("Failed to parse JSON from response")
                        return {"error": "Failed to parse JSON from response", "raw_content": content}

        except Exception as e:
            self.logger.error(f"Error generating JSON: {str(e)}")
            return {"error": f"Error generating JSON: {str(e)}"}

    def use_function_calling(self,
                             system_prompt: str,
                             user_prompt: str,
                             functions: List[Dict[str, Any]],
                             function_name: Optional[str] = None,
                             model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Usa a API de function calling para executar uma função específica
        """
        try:
            self.logger.info(f"Using function calling with {model}")

            # Configurar function calling
            tools = [{"type": "function", "function": func}
                     for func in functions]

            # Configurar tool_choice se um nome de função específico for fornecido
            tool_choice = "auto"
            if function_name:
                tool_choice = {"type": "function",
                               "function": {"name": function_name}}

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice=tool_choice
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            if tool_calls:
                function_response = {
                    "function_name": tool_calls[0].function.name,
                    "arguments": json.loads(tool_calls[0].function.arguments)
                }
                return function_response
            else:
                return {"content": message.content, "no_function_call": True}

        except Exception as e:
            self.logger.error(f"Error using function calling: {str(e)}")
            return {"error": f"Error using function calling: {str(e)}"}

    def evaluate_speech(self,
                        spoken_text: str,
                        expected_text: str,
                        difficulty: str = "medium") -> Dict[str, Any]:
        """
        Avalia a pronúncia do texto falado comparado com o esperado
        """
        functions = [
            {
                "name": "provide_evaluation",
                "description": "Avaliar precisão da pronúncia da fala",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "accuracy_score": {
                            "type": "integer",
                            "description": "Pontuação de precisão da pronúncia de 1-10"
                        },
                        "matched_sounds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Sons que foram pronunciados corretamente"
                        },
                        "challenging_sounds": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Sons que precisam de melhoria"
                        },
                        "detailed_feedback": {
                            "type": "string",
                            "description": "Avaliação técnica da pronúncia"
                        },
                        "suggested_exercises": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Exercícios recomendados para praticar os sons problemáticos"
                        }
                    },
                    "required": ["accuracy_score", "matched_sounds", "challenging_sounds", "detailed_feedback"]
                }
            }
        ]

        system_prompt = f"""És um patologista da fala especializado na avaliação da pronúncia de crianças.
Avalia quão próxima está a fala da criança da palavra ou frase esperada.
Sê detalhado na tua análise de sons específicos e fonemas do português.
O nível de dificuldade atual é: {difficulty}. Ajusta a tua avaliação conforme apropriado para este nível.
Identifice fonemas específicos que foram pronunciados corretamente e incorretamente.
"""

        user_prompt = f"Texto esperado: '{expected_text}'\nTexto falado: '{spoken_text}'\n\nFornece uma avaliação detalhada da pronúncia da criança."

        result = self.use_function_calling(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            functions=functions,
            function_name="provide_evaluation"
        )

        if "arguments" in result:
            return result["arguments"]
        else:
            # Fallback response
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(
                None, spoken_text.lower(), expected_text.lower()).ratio()

            return {
                "accuracy_score": int(similarity * 10),
                "matched_sounds": [],
                "challenging_sounds": [],
                "detailed_feedback": "Não foi possível analisar a pronúncia em detalhe."
            }

    def create_game_content(self,
                            game_type: str,
                            difficulty: str,
                            age_group: str,
                            target_sound: str) -> Dict[str, Any]:
        """
        Cria conteúdo para um jogo de terapia da fala
        """
        system_prompt = f"""És um especialista em terapia da fala para {age_group} falantes de português.

# CONTEXTO
Estás a criar jogos para uma aplicação de terapia da fala que ajuda {age_group} a melhorar as suas competências de comunicação.
O jogo deve ser adequado para o nível de dificuldade '{difficulty}' e focar no tipo '{game_type}'.

# FORMATO DE SAÍDA
Responde com um objeto JSON contendo:
- "title": título criativo do jogo
- "description": breve descrição do objetivo
- "instructions": lista de instruções claras
- "exercises": lista com 5 exercícios específicos
- "target_skills": lista de competências desenvolvidas
- "target_sound": som-alvo do jogo (ex.: "s", "r")
- "estimated_duration": tempo estimado (ex.: "5-10 minutos")
- "theme": tema visual para o jogo
- "visual_style": estilo visual sugerido
"""

        user_prompt = f"Crie um jogo de terapia da fala do tipo '{game_type}' em português para {age_group}, nível '{difficulty}', focado no som '{target_sound}'. Inclua um título criativo, descrição, instruções claras (em lista), 5 exercícios e metadados."

        return self.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8
        )

    def perform_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Realiza uma busca na web usando a Google Search API

        Args:
            query: Consulta de busca
            num_results: Número de resultados desejados

        Returns:
            Lista de resultados da busca
        """
        if not self.search_enabled:
            self.logger.warning(
                "Tentativa de busca, mas a ferramenta de busca não está disponível")
            return [{"error": "Ferramenta de busca não disponível"}]

        return self.search_tool.search(query, num_results=num_results)

    def find_therapy_resources(self, sound: str, difficulty: str, age_group: str = "crianças") -> Dict[str, Any]:
        """
        Busca recursos de terapia da fala e sintetiza informações relevantes

        Args:
            sound: Som/fonema alvo
            difficulty: Nível de dificuldade
            age_group: Grupo etário

        Returns:
            Informações consolidadas sobre técnicas terapêuticas
        """
        if not self.search_enabled:
            self.logger.warning(
                "Tentativa de busca de recursos, mas a ferramenta não está disponível")
            return {"error": "Ferramenta de busca não disponível"}

        # Realizar busca por recursos terapêuticos
        search_results = self.search_tool.search_therapy_exercise(
            sound, difficulty, age_group)

        # Sintetizar os resultados usando o LLM
        if search_results:
            # Preparar contexto para o LLM
            context = "Recursos de terapia encontrados:\n\n"
            for i, result in enumerate(search_results):
                context += f"{i+1}. {result.get('title', 'Sem título')}\n"
                context += f"   {result.get('snippet', 'Sem descrição')}\n"
                context += f"   Fonte: {result.get('link', 'Link não disponível')}\n\n"

            system_prompt = """Você é um assistente especializado em terapia da fala.
Sintetize as informações dos recursos encontrados para criar um resumo útil de técnicas terapêuticas.
Foque em exercícios práticos, técnicas de articulação e abordagens pedagógicas para o fonema específico.
Seu resumo deve incluir:
1. 2-3 exercícios específicos para praticar o fonema
2. Orientações sobre posicionamento correto da língua, lábios e fluxo de ar
3. Sugestões de palavras para praticar o som em diferentes posições (início, meio, fim)
"""

            user_prompt = f"""Fonema alvo: {sound}
Nível de dificuldade: {difficulty}
Grupo etário: {age_group}

Por favor, sintetize as técnicas terapêuticas mais relevantes dos seguintes recursos:

{context}
"""

            # Gerar síntese
            synthesis = self.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=800
            )

            # Estruturar a resposta
            return {
                "sound": sound,
                "difficulty": difficulty,
                "age_group": age_group,
                "synthesis": synthesis,
                "sources": [result.get("link") for result in search_results if "link" in result],
                "raw_results": search_results
            }
        else:
            return {
                "sound": sound,
                "difficulty": difficulty,
                "age_group": age_group,
                "synthesis": "Não foram encontrados recursos específicos para este som.",
                "sources": [],
                "raw_results": []
            }

    def generate_personalized_game(self,
                                   interest: str,
                                   sound: str,
                                   difficulty: str,
                                   age_group: str = "crianças") -> Dict[str, Any]:
        """
        Gera um jogo personalizado baseado nos interesses do usuário e pesquisa na web

        Args:
            interest: Interesse do usuário (ex: "dinossauros", "futebol")
            sound: Som/fonema alvo
            difficulty: Nível de dificuldade
            age_group: Grupo etário

        Returns:
            Jogo personalizado com elementos relacionados ao interesse do usuário
        """
        self.logger.info(
            f"Gerando jogo personalizado sobre {interest} para o som {sound}")

        # Buscar informações relevantes sobre o interesse do usuário
        interest_info = {}
        if self.search_enabled:
            # Buscar informações sobre o interesse em relação à terapia
            interest_data = self.search_tool.search_personalized_activity(
                interest, sound, difficulty)
            if "suggestions" in interest_data and interest_data["suggestions"]:
                interest_info = interest_data

        # Preparar contexto para geração do jogo
        extra_context = ""
        if interest_info and "suggestions" in interest_info:
            extra_context = "Informações relacionadas ao interesse do usuário:\n"
            for i, suggestion in enumerate(interest_info.get("suggestions", [])):
                extra_context += f"- {suggestion}\n"

        # Prompt para gerar jogo personalizado
        system_prompt = f"""Você é um especialista em terapia da fala para {age_group} que cria jogos educativos.
Crie um jogo divertido que combine o interesse do usuário em {interest} com exercícios para praticar o som '{sound}'.
O jogo deve ser adequado para o nível de dificuldade '{difficulty}'.

# FORMATO DE SAÍDA
Responda com um objeto JSON contendo:
- "title": título criativo do jogo relacionado ao tema {interest}
- "description": breve descrição do objetivo
- "instructions": lista de instruções claras
- "exercises": lista com 5 exercícios específicos usando palavras com o som '{sound}' relacionadas a {interest}
- "target_skills": lista de competências desenvolvidas
- "theme": {interest}
- "estimated_duration": tempo estimado (ex.: "5-10 minutos")
"""

        user_prompt = f"""Crie um jogo de terapia da fala personalizado com as seguintes características:
- Tema de interesse do usuário: {interest}
- Som a ser trabalhado: '{sound}'
- Nível de dificuldade: {difficulty}
- Grupo etário: {age_group}

{extra_context}

Inclua palavras relacionadas a {interest} que contenham o som '{sound}' nos exercícios.
"""

        # Gerar o jogo personalizado
        try:
            game_json = self.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )

            # Adicionar metadados
            game_json["metadata"] = {
                "interest": interest,
                "sound": sound,
                "difficulty": difficulty,
                "age_group": age_group,
                "personalized": True,
                "search_enhanced": self.search_enabled
            }

            return game_json
        except Exception as e:
            self.logger.error(f"Erro ao gerar jogo personalizado: {str(e)}")
            return {
                "error": f"Erro ao gerar jogo personalizado: {str(e)}",
                "title": f"Jogo sobre {interest}",
                "description": f"Um jogo para praticar o som '{sound}'",
                "exercises": [
                    {"word": "Jogo não disponível",
                        "prompt": "Tente novamente mais tarde"}
                ]
            }

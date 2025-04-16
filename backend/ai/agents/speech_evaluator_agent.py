from typing import Dict, List, Any, Optional
import json
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SpeechEvaluatorAgent:
    """Agent responsible for evaluating speech pronunciation"""

    def __init__(self, client=None):
        load_dotenv()
        if client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required for SpeechEvaluatorAgent")
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = client
        self.logger = logging.getLogger("SpeechEvaluatorAgent")
        self.logger.info("SpeechEvaluatorAgent initialized")

        # Dicionário de fonemas portugueses e suas características
        self.phonetic_map = {
            'r': {'type': 'consoante', 'difficulty': 'alta', 'common_issues': ['substituição por l', 'omissão']},
            'rr': {'type': 'consoante', 'difficulty': 'alta', 'common_issues': ['substituição por r']},
            'l': {'type': 'consoante', 'difficulty': 'média', 'common_issues': ['omissão']},
            's': {'type': 'consoante', 'difficulty': 'média', 'common_issues': ['substituição por t']},
            'ch': {'type': 'consoante', 'difficulty': 'alta', 'common_issues': ['substituição por s', 'substituição por t']},
            'lh': {'type': 'consoante', 'difficulty': 'alta', 'common_issues': ['substituição por l', 'substituição por y']},
            'nh': {'type': 'consoante', 'difficulty': 'alta', 'common_issues': ['substituição por n']}
        }

    def evaluate_speech(self, spoken_text: str, expected_text: str, difficulty: str = "medium") -> Dict[str, Any]:
        """
        Avalia a precisão da fala comparando o texto falado com o esperado
        Retorna pontuação, precisão e detalhes sobre a pronúncia
        """
        self.logger.info(
            f"Avaliando: '{spoken_text}' | Esperado: '{expected_text}'")

        # Cálculo básico de similaridade como backup
        similarity = self._calculate_string_similarity(
            spoken_text.lower(), expected_text.lower())

        # Avaliação detalhada usando IA
        detailed_evaluation = self._get_ai_pronunciation_analysis(
            spoken_text, expected_text, difficulty)

        # Combinar resultados básicos com avaliação da IA
        accuracy = detailed_evaluation.get(
            "accuracy_score", similarity * 10) / 10.0

        result = {
            "accuracy": min(max(accuracy, 0.0), 1.0),  # Normalizar entre 0 e 1
            "score": int(accuracy * 100),
            "expected_text": expected_text,
            "spoken_text": spoken_text,
            "exact_match": spoken_text.lower() == expected_text.lower(),
            "improvement_areas": detailed_evaluation.get("challenging_sounds", []),
            "strengths": detailed_evaluation.get("matched_sounds", []),
            "details": {
                "phonetic_analysis": detailed_evaluation.get("detailed_feedback", ""),
                "phonemes_correct": detailed_evaluation.get("matched_sounds", []),
                "phonemes_incorrect": detailed_evaluation.get("challenging_sounds", []),
                "similarity_score": similarity
            }
        }

        # Adicionar sugestões específicas baseadas no nível de dificuldade
        result["suggestions"] = self._generate_targeted_suggestions(
            result["improvement_areas"],
            difficulty
        )

        return result

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calcula a similaridade entre duas strings usando SequenceMatcher"""
        return SequenceMatcher(None, str1, str2).ratio()

    def _get_ai_pronunciation_analysis(self, spoken_text: str, expected_text: str, difficulty: str) -> Dict[str, Any]:
        """Obtem análise detalhada da pronúncia usando IA"""
        try:
            tools = [
                {
                    "type": "function",
                    "function": {
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
                }
            ]

            system_prompt = f"""És um patologista da fala especializado na avaliação da pronúncia de crianças.
Avalia quão próxima está a fala da criança da palavra ou frase esperada.
Sê detalhado na tua análise de sons específicos e fonemas do português.
O nível de dificuldade atual é: {difficulty}. Ajusta a tua avaliação conforme apropriado para este nível.
Identifice fonemas específicos que foram pronunciados corretamente e incorretamente.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # usando um modelo mais leve para resposta rápida
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto esperado: '{expected_text}'\nTexto falado: '{spoken_text}'\n\nFornece uma avaliação detalhada da pronúncia da criança."}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {
                    "name": "provide_evaluation"}}
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            if tool_calls:
                evaluation = json.loads(tool_calls[0].function.arguments)
                self.logger.info(
                    f"Avaliação de pronúncia obtida para '{expected_text}'")
                return evaluation

        except Exception as e:
            self.logger.error(f"Erro ao avaliar pronúncia: {str(e)}")

        # Avaliação de fallback
        return {
            "accuracy_score": int(self._calculate_string_similarity(spoken_text.lower(), expected_text.lower()) * 10),
            "matched_sounds": [],
            "challenging_sounds": [],
            "detailed_feedback": "Não foi possível analisar a pronúncia em detalhe."
        }

    def _generate_targeted_suggestions(self, problem_areas: List[str], difficulty: str) -> List[str]:
        """Gera sugestões específicas baseadas nas áreas problemáticas identificadas"""
        suggestions = []

        difficulty_level = {"easy": 0, "medium": 1,
                            "hard": 2}.get(difficulty.lower(), 1)

        exercise_templates = [
            [  # Fácil
                "Repita a palavra lentamente, som por som: {sound}",
                "Pratique dizendo '{sound}' no início de palavras simples",
                "Observe meus lábios quando eu digo '{sound}'"
            ],
            [  # Médio
                "Tente contrastar '{sound}' com sons similares",
                "Pratique palavras que começam e terminam com '{sound}'",
                "Repita frases curtas contendo o som '{sound}'"
            ],
            [  # Difícil
                "Use espelho para observar posição da língua ao dizer '{sound}'",
                "Pratique palavras com múltiplas ocorrências de '{sound}'",
                "Grave-se dizendo palavras com '{sound}' e compare com a pronúncia correta"
            ]
        ]

        # Limitar a 3 sugestões para não sobrecarregar
        for area in problem_areas[:3]:
            template = np.random.choice(exercise_templates[difficulty_level])
            suggestions.append(template.format(sound=area))

        return suggestions

    def analyze_progress(self, user_id: str, session_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa o progresso do usuário ao longo do tempo
        """
        if not session_history:
            return {
                "progress": 0,
                "consistent_issues": [],
                "improving_areas": [],
                "recommendation": "Necessário mais dados para análise de progresso"
            }

        # Extrair métricas relevantes
        accuracy_trend = [session.get("accuracy", 0)
                          for session in session_history]

        # Calcular métricas de progresso
        progress = 0
        if len(accuracy_trend) >= 2:
            # Média ponderada com ênfase nas sessões mais recentes
            weights = np.linspace(0.5, 1.0, len(accuracy_trend))
            weighted_avg = np.average(accuracy_trend, weights=weights)

            # Tendência recente (últimas 3 sessões ou todas se menos que 3)
            recent_trend = accuracy_trend[-min(3, len(accuracy_trend)):]
            recent_progress = recent_trend[-1] - \
                recent_trend[0] if len(recent_trend) > 1 else 0

            progress = (weighted_avg * 0.7) + (recent_progress * 0.3)

        # Identificar problemas consistentes e áreas de melhoria
        all_issues = []
        for session in session_history:
            all_issues.extend(session.get("improvement_areas", []))

        # Contar frequência dos problemas
        from collections import Counter
        issue_counts = Counter(all_issues)

        # Problemas que aparecem em pelo menos 50% das sessões são considerados consistentes
        min_sessions = max(2, len(session_history) // 2)
        consistent_issues = [
            issue for issue, count in issue_counts.items() if count >= min_sessions]

        result = {
            "progress": max(0, min(progress, 1.0)),  # Normalizar entre 0 e 1
            "consistent_issues": consistent_issues,
            # Precisaria de lógica mais complexa para identificar melhoria por área
            "improving_areas": [],
            "recommendation": self._generate_progress_recommendation(progress, consistent_issues)
        }

        return result

    def _generate_progress_recommendation(self, progress: float, consistent_issues: List[str]) -> str:
        """Gera recomendação baseada no progresso e problemas consistentes"""
        if progress < 0.2:
            return "Recomendamos exercícios básicos de articulação e consciência fonológica."
        elif progress < 0.5:
            if consistent_issues:
                return f"Continue praticando com foco nos sons: {', '.join(consistent_issues[:3])}"
            return "Continue praticando com exercícios variados para desenvolver diferentes sons."
        elif progress < 0.8:
            return "Bom progresso! Recomendamos aumentar a complexidade das frases e introduzir mais velocidade na fala."
        else:
            return "Excelente progresso! Recomendamos praticar com narrativas mais longas e situações de conversação."

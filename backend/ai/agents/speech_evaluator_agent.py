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

    def evaluate_speech(self, spoken_text: str, expected_text: str, difficulty: str = "medium") -> dict:
        """
        Avalia a precisão da pronúncia comparando o texto falado com o esperado.
        Foca APENAS na lógica de avaliação principal (ex: chamada OpenAI).
        """
        self.logger.info(
            f"Avaliando: '{spoken_text}' | Esperado: '{expected_text}'")
        try:
            # --- Lógica Principal de Avaliação ---
            # Exemplo: Usar OpenAI para comparar os textos e obter detalhes fonéticos
            # (Substitua pelo seu prompt e lógica real)
            prompt = f"""
            Avalie a pronúncia da palavra "{expected_text}" quando o usuário disse "{spoken_text}".
            Forneça uma pontuação de precisão de 0.0 a 1.0.
            Liste os sons que foram bem pronunciados (strengths).
            Liste as áreas de melhoria ou sons desafiadores (improvement_areas).
            Forneça uma análise fonética curta (phonetic_analysis).
            Responda em formato JSON com as chaves: "accuracy", "strengths", "improvement_areas", "details": {{"phonetic_analysis": "..."}}.
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Ou o modelo apropriado
                messages=[{"role": "user", "content": prompt}],
                # Se suportado e desejado
                response_format={"type": "json_object"}
            )

            evaluation_result = json.loads(response.choices[0].message.content)

            # Adicionar pontuação de 0 a 10 baseada na precisão
            evaluation_result["score"] = int(
                evaluation_result.get("accuracy", 0.0) * 10)

            # --- NOVO: Mascarar campos grandes antes de logar ---
            log_result = evaluation_result.copy()  # Criar cópia para não alterar o original
            # Verificar se existe um campo de áudio e se ele é uma string longa
            # Limite de exemplo: 100 caracteres
            if "audio_feedback" in log_result and isinstance(log_result["audio_feedback"], str) and len(log_result["audio_feedback"]) > 100:
                # Substituir por placeholder com tamanho
                log_result["audio_feedback"] = f"<audio_data len={len(log_result['audio_feedback'])}>"

            # Logar a versão mascarada/modificada
            self.logger.info(f"Resultado da avaliação: {log_result}")
            # --- FIM DA MODIFICAÇÃO ---

            return evaluation_result  # Retornar o resultado original completo

        except Exception as e:
            self.logger.error(f"Erro durante a avaliação da fala: {e}")
            # Retornar uma estrutura de erro padrão
            return {
                "accuracy": 0.0,
                "score": 0,
                "strengths": [],
                "improvement_areas": ["Erro na avaliação"],
                "details": {"phonetic_analysis": f"Falha ao avaliar: {e}"}
            }

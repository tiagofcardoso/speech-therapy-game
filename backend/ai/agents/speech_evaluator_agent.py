from typing import Dict, List, Any, Optional
import json
import logging
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from difflib import SequenceMatcher
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SpeechEvaluatorAgent(BaseAgent):
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

    async def evaluate_speech(self, spoken_text: str, expected_text: str,
                              difficulty: str = "medium") -> dict:
        """Async version of evaluate_speech"""
        try:
            # Use the same prompt as before
            prompt = f"""
            Avalie a pronúncia da palavra "{expected_text}" quando o usuário disse "{spoken_text}".
            # ... rest of the prompt ...
            """

            # Use async version of OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            evaluation_result = json.loads(response.choices[0].message.content)
            evaluation_result["score"] = int(
                evaluation_result.get("accuracy", 0.0) * 10)

            return evaluation_result
        except Exception as e:
            self.logger.error(f"Error evaluating speech: {str(e)}")
            # Return a basic error result
            return {
                "accuracy": 0.0,
                "score": 0,
                "strengths": [],
                "improvement_areas": ["Could not evaluate speech"],
                "details": {"phonetic_analysis": f"Error: {str(e)}"}
            }

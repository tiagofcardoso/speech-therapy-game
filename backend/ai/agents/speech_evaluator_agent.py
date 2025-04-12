from typing import Dict, List, Any
import json


class SpeechEvaluatorAgent:
    """Agent responsible for evaluating speech pronunciation"""

    def __init__(self, client):
        self.client = client

    def evaluate_pronunciation(self, spoken_text: str, expected_word: str, hint: str) -> Dict:
        """Evaluate how well the spoken text matches the expected word"""

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "provide_evaluation",
                    "description": "Evaluate speech pronunciation accuracy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "accuracy_score": {
                                "type": "integer",
                                "description": "Pronunciation accuracy score from 1-10"
                            },
                            "matched_sounds": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Sounds that were pronounced correctly"
                            },
                            "challenging_sounds": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Sounds that need improvement"
                            },
                            "detailed_feedback": {
                                "type": "string",
                                "description": "Technical assessment of the pronunciation"
                            }
                        },
                        "required": ["accuracy_score", "matched_sounds", "challenging_sounds", "detailed_feedback"]
                    }
                }
            }
        ]

        system_prompt = """És um patologista da fala especializado na avaliação da pronúncia de crianças.
Avalia quão próxima está a fala da criança da palavra esperada.
Sê detalhado na tua análise de sons específicos e fonemas.
Sê encorajador mas honesto sobre as áreas que necessitam de melhorias.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Expected word: '{expected_word}'\nSpoken text: '{spoken_text}'\nPronunciation hint: {hint}\n\nProvide a detailed evaluation of the child's pronunciation."}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {
                    "name": "provide_evaluation"}}
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            if tool_calls:
                evaluation = json.loads(tool_calls[0].function.arguments)
                return evaluation

        except Exception as e:
            print(f"Error evaluating pronunciation: {e}")

        # Fallback evaluation
        return {
            "accuracy_score": 5,
            "matched_sounds": [],
            "challenging_sounds": [],
            "detailed_feedback": "Unable to analyze pronunciation in detail."
        }

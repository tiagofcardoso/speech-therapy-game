from typing import Optional, Dict, Any, List
import logging
import re
import json
import base64
from openai import AsyncOpenAI
from ..server.openai_client import create_async_openai_client
from .base_agent import BaseAgent
from rapidfuzz import fuzz

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SpeechEvaluatorAgent(BaseAgent):
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        self.client = client or create_async_openai_client()
        self.logger = logging.getLogger(__name__)
        self.logger.info("SpeechEvaluatorAgent initialized")

    async def initialize(self):
        """Initialize the agent if needed"""
        # Nothing to initialize for now
        self.logger.info("SpeechEvaluatorAgent initialization complete")
        return True

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better comparison by removing punctuation, extra spaces, 
        and converting to lowercase.

        Now also handles compound words with or without hyphens and normalizes them.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Replace hyphens with spaces for compound word flexibility
        text = text.replace('-', ' ')

        # Remove punctuation except apostrophes (for contractions)
        text = re.sub(r'[^\w\s\']', '', text)

        # Replace multiple spaces with a single space and trim
        text = re.sub(r'\s+', ' ', text).strip()

        self.logger.debug(f"Normalized text: '{text}' (from original)")
        return text

    def _handle_compound_words(self, recognized: str, expected: str) -> tuple:
        """
        Special handling for compound words to improve matching.
        Returns both normalized versions and a flag indicating if compound word handling was applied.
        """
        # Check if expected might be a compound word (contains hyphen or multiple words)
        is_compound = '-' in expected or ' ' in expected.strip()
        compound_normalized_expected = expected.replace(
            '-', '').replace(' ', '')

        # Try to detect if recognized might be the compound word written as separate words
        normalized_recognized = recognized.replace(' ', '')

        # Create no-space versions for direct comparison
        no_space_recognized = recognized.replace(' ', '')
        no_space_expected = expected.replace(' ', '').replace('-', '')

        # Check if removing spaces makes them identical
        if no_space_recognized == no_space_expected:
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Compound word match detected: '{recognized}' matches '{expected}' when ignoring spaces/hyphens")
            return normalized_recognized, no_space_expected, True

        self.logger.debug(
            f"[AGENT:SPEECH_EVALUATOR] Compound word check: is_compound={is_compound}, match={no_space_recognized == no_space_expected}")
        return recognized, expected, is_compound

    async def evaluate_pronunciation(self, recognized_text: str, expected_word: str) -> Dict[str, Any]:
        """
        Evaluate pronunciation by comparing recognized text with expected word.
        Enhanced with better handling of compound words and fuzzy matching.
        """
        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Starting evaluation of: '{recognized_text}' vs expected '{expected_word}'")

        # If no recognized text, return failure immediately
        if not recognized_text:
            self.logger.warning(
                "[AGENT:SPEECH_EVALUATOR] No recognized text provided")
            return {
                "isCorrect": False,
                "score": 0,
                "feedback": f"Não consegui entender. Tente pronunciar '{expected_word}' novamente, de forma clara.",
            }

        # Normalize both texts for comparison
        norm_recognized = self._normalize_text(recognized_text)
        norm_expected = self._normalize_text(expected_word)

        # Apply special handling for compound words
        norm_recognized, norm_expected, is_compound = self._handle_compound_words(
            norm_recognized, norm_expected)

        # Log normalized versions for debugging
        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Normalized for comparison: '{norm_recognized}' vs '{norm_expected}'")

        # Exact match check
        is_exact_match = norm_recognized == norm_expected

        # Check if expected word is contained in recognized text
        is_contained = norm_expected in norm_recognized

        # For short words, use fuzzy matching with higher threshold
        word_similarity = fuzz.ratio(norm_recognized, norm_expected)
        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Word similarity score: {word_similarity}%")

        # For compound words or short words, use a lower threshold
        similarity_threshold = 80 if len(
            norm_expected) <= 4 or is_compound else 90
        is_similar = word_similarity >= similarity_threshold

        # Special case for compound words: check if removing spaces makes them match
        no_space_match = norm_recognized.replace(
            " ", "") == norm_expected.replace(" ", "").replace("-", "")

        # Determine result based on various matching strategies
        if is_exact_match or no_space_match:
            is_correct = True
            score = 10
            # Use the original expected_word with hyphens in the feedback for clarity
            feedback = f"Excelente pronúncia de '{expected_word}'! Perfeito!"
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Exact or no-space match detected → Perfect score (10)")
        elif is_similar:
            is_correct = True
            score = 8
            feedback = f"Boa pronúncia de '{expected_word}'! Quase perfeito."
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Similar pronunciation detected → Good score (8)")
        elif is_contained:
            is_correct = True
            score = 7
            feedback = f"Reconheci '{expected_word}' na sua pronúncia. Continue praticando!"
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Word contained in speech → Acceptable score (7)")
        else:
            is_correct = False
            score = max(1, int(word_similarity / 20))
            feedback = f"Tente novamente. Eu ouvi '{recognized_text}' mas esperava '{expected_word}'."
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] No match detected → Low score ({score})")

        # Add debug info
        debug_info = {
            "original": {
                "recognized": recognized_text,
                "expected": expected_word
            },
            "normalized": {
                "recognized": norm_recognized,
                "expected": norm_expected
            },
            "similarity_score": word_similarity,
            "is_compound_word": is_compound,
            "no_space_match": no_space_match
        }

        # Return evaluation result
        result = {
            "isCorrect": is_correct,
            "score": score,
            "feedback": feedback,
            "debug_info": debug_info
        }

        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Evaluation complete: {json.dumps(result, indent=2)}")
        return result

    async def evaluate_audio(self, audio_data, expected_word: str) -> Dict[str, Any]:
        """Evaluate audio data against expected word"""
        try:
            # Implementation would depend on what audio_data contains and what recognition method is used
            # This would typically call a speech recognition service and then evaluate the result
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Audio evaluation for word: {expected_word} is not implemented")

            # Returning a placeholder result - in a real implementation this would process the audio
            return {
                "isCorrect": True,
                "score": 8,
                "feedback": f"Audio evaluation for {expected_word} not implemented yet"
            }
        except Exception as e:
            self.logger.error(
                f"[AGENT:SPEECH_EVALUATOR] Error evaluating audio: {str(e)}")
            return {
                "isCorrect": False,
                "score": 0,
                "feedback": f"Error evaluating audio: {str(e)}"
            }

    def generate_feedback(self, is_correct: bool, score: int, recognized_text: str, expected_word: str) -> str:
        """
        Generate appropriate feedback based on evaluation results
        """
        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Generating feedback for: correct={is_correct}, score={score}")

        if not is_correct:
            if not recognized_text or recognized_text == "":
                feedback = f"Não consegui entender. Tente pronunciar '{expected_word}' novamente, de forma clara."
            else:
                feedback = f"Tente novamente. Eu ouvi '{recognized_text}' mas esperava '{expected_word}'."
        else:
            if score >= 9:
                feedback = f"Excelente pronúncia de '{expected_word}'! Perfeito!"
            elif score >= 7:
                feedback = f"Boa pronúncia de '{expected_word}'! Continue assim."
            else:
                feedback = f"Reconheci '{expected_word}' na sua pronúncia. Continue praticando!"

        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Generated feedback: '{feedback}'")
        return feedback

from typing import Optional, Dict, Any, List
import logging
import re
import json
import base64
from openai import AsyncOpenAI
from ..server.openai_client import create_async_openai_client
from .base_agent import BaseAgent
from utils.agent_logger import log_agent_call
from rapidfuzz import fuzz

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SpeechEvaluatorAgent(BaseAgent):
    def __init__(self, client: Optional[AsyncOpenAI] = None):
        super().__init__(name="SPEECH_EVALUATOR")
        self.client = client or create_async_openai_client()
        self.logger.info("SpeechEvaluatorAgent initialized")

    @log_agent_call
    async def initialize(self):
        """Initialize the agent if needed"""
        self.logger.info("Initialization complete")
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
                f"Compound word match detected: '{recognized}' matches '{expected}' when ignoring spaces/hyphens")
            return normalized_recognized, no_space_expected, True

        self.logger.debug(
            f"[AGENT:SPEECH_EVALUATOR] Compound word check: is_compound={is_compound}, match={no_space_recognized == no_space_expected}")
        return recognized, expected, is_compound

    def _handle_sentence_comparison(self, recognized: str, expected: str) -> bool:
        """
        Special handling for longer phrases and tongue twisters with common recognition errors.
        Returns True if the phrases are similar enough to be considered correct.
        """
        # If they're almost identical, return early
        if self._similarity_score(recognized, expected) > 90:
            return True

        # Handle common Portuguese recognition issues
        recognized_fixed = recognized

        # Common mistake: "Globo" instead of "O lobo"
        if "globo" in recognized.lower() and "o lobo" in expected.lower():
            recognized_fixed = recognized.lower().replace("globo", "o lobo")
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Applied Portuguese-specific fix: 'globo' -> 'o lobo'")

        # Common mistake: "Ou" instead of "O"
        if expected.lower().startswith("o ") and recognized.lower().startswith("ou "):
            recognized_fixed = "o " + recognized[3:]
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Applied Portuguese-specific fix: 'ou ' -> 'o '")

        # Common issue with articles
        if expected.lower().startswith("a ") and not recognized.lower().startswith("a "):
            recognized_fixed = "a " + recognized
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Added missing article 'a' at beginning")

        # Check word count - if matching at least 80% of words in the right order, consider it correct
        expected_words = expected.lower().split()
        recognized_words = recognized_fixed.lower().split()

        matching_words = 0
        for i, word in enumerate(expected_words):
            if i < len(recognized_words) and (
                recognized_words[i] == word or
                self._similarity_score(recognized_words[i], word) > 85
            ):
                matching_words += 1

        word_match_ratio = matching_words / \
            len(expected_words) if expected_words else 0
        self.logger.info(
            f"[AGENT:SPEECH_EVALUATOR] Word match ratio: {word_match_ratio:.2f} ({matching_words}/{len(expected_words)})")

        # For tongue twisters, be more forgiving (threshold 0.7)
        is_tongue_twister = len(expected_words) > 5 and len(
            set(expected_words)) < len(expected_words) * 0.8
        threshold = 0.7 if is_tongue_twister else 0.8

        return word_match_ratio >= threshold

    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0-100)"""
        from rapidfuzz import fuzz
        return fuzz.ratio(str1.lower(), str2.lower())

    @log_agent_call
    async def evaluate_pronunciation(self, recognized_text: str, expected_word: str) -> Dict[str, Any]:
        """
        Evaluate pronunciation by comparing recognized text with expected word or phrase.
        Enhanced with better handling of sentences and tongue twisters.
        """
        self.logger.info(
            f"Starting evaluation of: '{recognized_text}' vs expected '{expected_word}'")

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

        # Check if this is a sentence (more than 3 words)
        is_sentence = len(norm_expected.split()) > 3

        # For sentences, use special handling
        if is_sentence:
            sentence_is_correct = self._handle_sentence_comparison(
                norm_recognized, norm_expected)
            self.logger.info(
                f"[AGENT:SPEECH_EVALUATOR] Sentence evaluation result: {sentence_is_correct}")

            if sentence_is_correct:
                return {
                    "isCorrect": True,
                    "score": 8,  # Good but not perfect
                    "feedback": f"Boa pronúncia da frase! Continue praticando para aperfeiçoar.",
                    "debug_info": {
                        "is_sentence": True,
                        "sentence_match": True,
                        "original": {
                            "recognized": recognized_text,
                            "expected": expected_word
                        }
                    }
                }

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

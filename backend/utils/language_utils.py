"""
Utility functions for language processing and Portuguese word variants
"""
import json
import os
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Common Portuguese tongue twisters for practice
PORTUGUESE_TONGUE_TWISTERS = [
    "O rato roeu a roupa do rei de Roma.",
    "Três tigres tristes para três pratos de trigo.",
    "O lobo ladrão leva lagostas para o lago.",
    "A aranha arranha a rã. A rã arranha a aranha.",
    "Sabendo o que sei e sabendo o que sabes e o que não sabes e o que não sabemos.",
    "Um ninho de mafagafos tem cinco mafagafinhos."
]


def load_pt_word_dictionary() -> List[Dict[str, str]]:
    """
    Load the Portuguese words dictionary that maps PT-PT to PT-BR variants

    Returns:
        List of word mappings with pt_pt, pt_br, and meaning fields
    """
    try:
        dict_path = Path(__file__).parent.parent / \
            "speech" / "words_pt_ptbr.json"

        if not os.path.exists(dict_path):
            logger.warning(
                f"Portuguese word dictionary not found at {dict_path}")
            return []

        with open(dict_path, 'r', encoding='utf-8') as f:
            word_dict = json.load(f)

        logger.info(
            f"Loaded Portuguese word dictionary with {len(word_dict)} entries")
        return word_dict
    except Exception as e:
        logger.error(f"Error loading Portuguese word dictionary: {str(e)}")
        return []


def get_pt_avoid_examples(max_examples: int = 10) -> str:
    """
    Get examples of PT-BR words to avoid with their PT-PT equivalents

    Args:
        max_examples: Maximum number of examples to include

    Returns:
        Formatted string with examples to include in LLM prompts
    """
    try:
        word_dict = load_pt_word_dictionary()
        if not word_dict:
            return ""

        # Select a subset of the most common/relevant examples
        examples = word_dict[:max_examples]

        # Format as a list of substitutions
        formatted_examples = "\n".join([
            f"- Use '{item['pt_pt']}' instead of '{item['pt_br']}' ({item['meaning']})"
            for item in examples
        ])

        return f"""
Examples of Brazilian Portuguese (PT-BR) words to AVOID and their European Portuguese (PT-PT) equivalents:

{formatted_examples}
"""
    except Exception as e:
        logger.error(f"Error generating PT avoid examples: {str(e)}")
        return ""


def is_tongue_twister(text: str) -> bool:
    """Check if a text is likely a tongue twister in Portuguese"""
    # Check if it's one of the known tongue twisters
    for twister in PORTUGUESE_TONGUE_TWISTERS:
        if text.lower() in twister.lower() or twister.lower() in text.lower():
            return True

    # Check for repeating sounds/syllables
    words = text.lower().split()
    if len(words) < 4:
        return False

    # Count repeating initial sounds
    initial_sounds = [word[:2] for word in words if len(word) > 1]
    sound_counts = {}
    for sound in initial_sounds:
        sound_counts[sound] = sound_counts.get(sound, 0) + 1

    # If any sound repeats 3+ times, likely a tongue twister
    if any(count >= 3 for count in sound_counts.values()):
        return True

    return False


def fix_common_recognition_errors(recognized: str, expected: str) -> str:
    """Fix common errors in Portuguese speech recognition"""
    fixed = recognized.lower()

    # Common replacements
    replacements = [
        ("globo", "o lobo"),
        ("ou ", "o "),
        ("ah ", "a "),
        ("uh ", "o ")
    ]

    for wrong, correct in replacements:
        if wrong in fixed and correct in expected.lower():
            fixed = fixed.replace(wrong, correct)
            logger.debug(f"Applied fix: '{wrong}' -> '{correct}'")

    return fixed


def evaluate_sentence_similarity(recognized: str, expected: str) -> Tuple[float, str]:
    """
    Evaluate the similarity between recognized and expected Portuguese sentences.
    Returns a tuple of (similarity_score, feedback)
    """
    from rapidfuzz import fuzz

    # Normalize texts
    norm_recognized = recognized.lower().strip()
    norm_expected = expected.lower().strip()

    # Full string similarity
    overall_ratio = fuzz.ratio(norm_recognized, norm_expected)

    # Word-by-word comparison
    expected_words = norm_expected.split()
    recognized_words = norm_recognized.split()

    # Count matching words
    matching_words = 0
    missing_words = []
    wrong_words = []

    for i, expected_word in enumerate(expected_words):
        if i < len(recognized_words):
            # Check if words match or are highly similar
            if recognized_words[i] == expected_word or fuzz.ratio(recognized_words[i], expected_word) > 85:
                matching_words += 1
            else:
                wrong_words.append((expected_word, recognized_words[i]))
        else:
            missing_words.append(expected_word)

    # Calculate word match percentage
    word_match_pct = (matching_words / len(expected_words)) * \
        100 if expected_words else 0

    # Generate appropriate feedback
    if word_match_pct > 90:
        feedback = "Excelente pronúncia da frase!"
    elif word_match_pct > 75:
        if missing_words:
            feedback = f"Boa pronúncia, mas faltaram algumas palavras como '{missing_words[0]}'."
        elif wrong_words:
            feedback = f"Boa pronúncia, mas a palavra '{wrong_words[0][0]}' foi reconhecida como '{wrong_words[0][1]}'."
        else:
            feedback = "Boa pronúncia da frase, mas pode melhorar ainda mais!"
    else:
        feedback = f"Tente novamente. Parece que você disse '{recognized}' em vez de '{expected}'."

    return (word_match_pct, feedback)

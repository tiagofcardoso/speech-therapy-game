"""
Utility functions for text processing and comparison in speech therapy applications.
Provides enhanced handling for compound words, monosyllabic words, and special
pronunciation cases in Portuguese.
"""

import re
from typing import Tuple, List, Dict, Any
from rapidfuzz import fuzz


def normalize_text(text: str) -> str:
    """
    Normalize text by removing punctuation, extra spaces, and converting to lowercase.

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove accents - optional, uncomment if needed
    # text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

    # Replace hyphens with spaces for compound word flexibility
    text = text.replace('-', ' ')

    # Remove punctuation except apostrophes
    text = re.sub(r'[^\w\s\']', '', text)

    # Replace multiple spaces with a single space and trim
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def is_compound_word(word: str) -> bool:
    """
    Check if a word is likely a compound word.

    Args:
        word: Word to check

    Returns:
        True if likely a compound word, False otherwise
    """
    return '-' in word or (len(word.split()) > 1)


def compare_with_compound_handling(recognized: str, expected: str) -> Dict[str, Any]:
    """
    Compare recognized text with expected text, with special handling for compound words.

    Args:
        recognized: Recognized text from speech recognition
        expected: Expected text to compare against

    Returns:
        Dictionary with comparison results
    """
    # Normalize both texts
    norm_recognized = normalize_text(recognized)
    norm_expected = normalize_text(expected)

    # Check if expected is a compound word
    is_compound = is_compound_word(expected)

    # Standard comparison metrics
    exact_match = norm_recognized == norm_expected
    contains_match = norm_expected in norm_recognized

    # Fuzzy match score
    similarity = fuzz.ratio(norm_recognized, norm_expected)

    # No-space comparison for compound words
    no_space_recognized = norm_recognized.replace(" ", "")
    no_space_expected = norm_expected.replace(" ", "")
    no_space_match = no_space_recognized == no_space_expected

    # Handle very short words differently
    is_short_word = len(norm_expected) <= 3

    # Determine appropriate threshold based on word characteristics
    threshold = 75 if is_short_word else (80 if is_compound else 90)

    # Overall match determination with special cases
    is_match = exact_match or no_space_match or (similarity >= threshold)

    # For compound words, if words are the same without spaces, it's a match
    if is_compound and no_space_match:
        is_match = True

    return {
        "is_match": is_match,
        "exact_match": exact_match,
        "contains_match": contains_match,
        "no_space_match": no_space_match,
        "similarity": similarity,
        "is_compound": is_compound,
        "is_short_word": is_short_word,
        "normalized": {
            "recognized": norm_recognized,
            "expected": norm_expected
        },
        "no_spaces": {
            "recognized": no_space_recognized,
            "expected": no_space_expected
        }
    }


def get_portuguese_phonetic_groups() -> Dict[str, List[str]]:
    """
    Get groups of phonetically similar sounds in Portuguese.
    Useful for understanding common pronunciation errors.

    Returns:
        Dictionary of phonetic groups
    """
    return {
        "similar_consonants": [
            ["b", "p"],  # Oclusivas bilabiais
            ["d", "t"],  # Oclusivas dentais
            ["g", "k"],  # Oclusivas velares
            ["v", "f"],  # Fricativas labiodentais
            ["z", "s"],  # Fricativas alveolares
            ["j", "ch"],  # Fricativas palatais
            ["m", "n"],  # Nasais
            ["l", "r"],  # Líquidas
            ["lh", "nh"],  # Palatais
        ],
        "similar_vowels": [
            ["a", "e"],  # Anterior não-arredondada
            ["e", "i"],  # Anterior não-arredondada
            ["o", "u"],  # Posterior arredondada
            ["ão", "am"],  # Nasais
            ["em", "en"],  # Nasais
        ]
    }


def analyze_pronunciation_error(recognized: str, expected: str) -> Dict[str, Any]:
    """
    Analyze pronunciation errors to provide more targeted feedback.

    Args:
        recognized: Recognized text
        expected: Expected text

    Returns:
        Dictionary with error analysis
    """
    comparison = compare_with_compound_handling(recognized, expected)

    if comparison["is_match"]:
        return {
            "has_error": False,
            "comparison": comparison,
            "feedback": f"Boa pronúncia de '{expected}'!"
        }

    # If not a match, analyze potential error types
    no_space_expected = comparison["no_spaces"]["expected"]
    no_space_recognized = comparison["no_spaces"]["recognized"]

    # Check for insertion/deletion/substitution errors
    if len(no_space_expected) > len(no_space_recognized):
        error_type = "omissão"
        suggestion = "pronuncie todas as sílabas claramente"
    elif len(no_space_expected) < len(no_space_recognized):
        error_type = "inserção"
        suggestion = "tente não adicionar sons extras"
    else:
        error_type = "substituição"
        suggestion = "preste atenção nos sons específicos"

    # For compound words, check if spaces/hyphens are the issue
    if comparison["is_compound"] and comparison["no_space_match"]:
        error_type = "composto"
        suggestion = "esta é uma palavra composta, pronuncie-a como uma única palavra"

    return {
        "has_error": True,
        "error_type": error_type,
        "suggestion": suggestion,
        "comparison": comparison,
        "feedback": f"Tente novamente com '{expected}'. {suggestion.capitalize()}."
    }

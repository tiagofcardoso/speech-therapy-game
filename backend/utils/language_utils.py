"""
Utility functions for language processing and Portuguese word variants
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


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

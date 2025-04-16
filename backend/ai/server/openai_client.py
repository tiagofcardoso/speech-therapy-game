import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
import json

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_openai_client() -> OpenAI:
    """Create and configure OpenAI client"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OpenAI API key found in environment")
        return None

    # Log that we're using the key (but don't show the full key)
    key_preview = "sk-" + "..." if api_key.startswith("sk-") else "..."
    logger.info(f"Using API key: {key_preview}")

    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {str(e)}")
        return None

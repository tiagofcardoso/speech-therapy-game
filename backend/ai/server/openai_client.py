import os
import logging
from openai import OpenAI, AsyncOpenAI  # Add AsyncOpenAI import

logger = logging.getLogger(__name__)


def create_openai_client(api_key=None):
    """Creates a synchronous OpenAI client"""
    try:
        # Explicitly load environment variables
        from dotenv import load_dotenv
        from pathlib import Path

        # Find the .env file at the project root
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent
        dotenv_path = project_root / '.env'

        # Load environment variables from .env
        if dotenv_path.exists():
            print(f"Loading .env file from: {dotenv_path}")
            load_dotenv(dotenv_path)
        else:
            print(f"Warning: .env file not found at {dotenv_path}")

        # Try to use the API key
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found")
            return None

        # Log first few characters for debugging
        print(f"Using API key: {api_key[:8]}...")

        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {str(e)}")
        return None


def create_async_openai_client(api_key=None):
    """Creates an asynchronous OpenAI client"""
    try:
        # Reuse API key loading logic
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not found")
            return None

        client = AsyncOpenAI(
            api_key=api_key,
            timeout=60.0  # Increased timeout for longer responses
        )
        logger.info("Async OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Error initializing async OpenAI client: {str(e)}")
        return None

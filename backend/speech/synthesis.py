import os
import base64
import tempfile
import logging
import boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# TTS Configuration
TTS_SERVICE = os.environ.get(
    "TTS_SERVICE", "AMAZON")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

# Voice settings for Portuguese (European)
DEFAULT_VOICE_SETTINGS = {
    "AMAZON": {
        "voice_id": "Ines",
        "engine": "standard",
        "language_code": "pt-PT",
        "sample_rate": "22050"
    },
    # Manter as configurações de outros serviços como fallback
    "AZURE": {
        "voice_name": "pt-PT-DuarteNeural",
        "style": "friendly",
        "rate": "1.0",
        "pitch": "0"
    },
    "GOOGLE": {
        "voice_name": "pt-PT-Wavenet-A",
        "speaking_rate": 1.0,
        "pitch": 0
    }
}

# Amazon Polly client singleton
_polly_client = None


def get_polly_client():
    """Get or create Amazon Polly client singleton"""
    global _polly_client
    if _polly_client is None:
        try:
            if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
                logger.error("AWS credentials not configured")
                return None

            _polly_client = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY,
                region_name=AWS_REGION
            ).client('polly')
            logger.info("Amazon Polly client initialized")
        except Exception as e:
            logger.error(f"Error initializing Amazon Polly client: {str(e)}")
            return None
    return _polly_client


def synthesize_speech(text, voice_settings=None):
    """
    Sintetiza fala a partir de texto.

    Args:
        text (str): Texto a ser sintetizado.
        voice_settings (dict, optional): Configurações da voz.

    Returns:
        bytes: Dados binários do áudio.
    """
    from gtts import gTTS
    import io

    try:
        print(f"🔊 Configurações de voz: {voice_settings}")

        # Usar o código de idioma apropriado, padrão pt-PT
        lang_code = voice_settings.get(
            'language_code', 'pt-PT') if voice_settings else 'pt-PT'

        # Mapear códigos de idioma compatíveis com gTTS
        lang_map = {
            'pt-PT': 'pt',
            'pt-BR': 'pt',
            'en-US': 'en',
            'es-ES': 'es'
        }

        # Usar o mapeamento ou o código original
        lang = lang_map.get(lang_code, lang_code.split('-')[0])

        # Criar objeto gTTS
        tts = gTTS(text=text, lang=lang)

        # Salvar em um buffer em memória
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        # Ler o conteúdo binário
        audio_bytes = mp3_fp.read()

        print(
            f"✅ Áudio sintetizado com sucesso. Tamanho: {len(audio_bytes)} bytes")
        return audio_bytes

    except Exception as e:
        print(f"❌ Erro na síntese de fala: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def _synthesize_amazon(text, custom_settings=None):
    """Synthesize speech using Amazon Polly"""
    try:
        # Get Polly client
        polly = get_polly_client()
        if not polly:
            logger.error("Failed to initialize Amazon Polly client")
            return None

        # Get voice settings
        settings = dict(DEFAULT_VOICE_SETTINGS["AMAZON"])
        if custom_settings:
            settings.update(custom_settings)

        # Use plain text instead of SSML for simplicity and compatibility
        # This resolves the "This voice does not support one of the used SSML features" error

        # Perform speech synthesis with plain text (no SSML)
        response = polly.synthesize_speech(
            Engine=settings["engine"],
            OutputFormat="mp3",
            SampleRate=settings["sample_rate"],
            Text=text,
            TextType="text",  # Always use plain text
            VoiceId=settings["voice_id"],
            LanguageCode=settings["language_code"]
        )

        # Check if we got a valid response with AudioStream
        if "AudioStream" not in response:
            logger.error("No AudioStream in Amazon Polly response")
            return None

        # Read and encode the audio stream
        audio_data = base64.b64encode(
            response["AudioStream"].read()).decode("utf-8")

        logger.info(
            f"Successfully synthesized text: '{text[:30]}...' with Amazon Polly")
        return audio_data

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        logger.error(f"Amazon Polly error ({error_code}): {error_message}")
        return None
    except Exception as e:
        logger.error(f"Error in Amazon speech synthesis: {str(e)}")
        return None


def get_available_voices():
    """Get list of available voices from Amazon Polly"""
    try:
        polly = get_polly_client()
        if not polly:
            return []

        # Use standard engine instead of neural to get compatible voices
        response = polly.describe_voices(
            Engine="standard",  # Changed from neural to standard
            LanguageCode="pt-PT"
        )

        voices = [{
            "id": voice["Id"],
            "name": voice["Name"],
            "gender": voice["Gender"],
            "language": voice["LanguageCode"]
        } for voice in response.get("Voices", [])]

        return voices
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        return []


def get_example_word_for_phoneme(phoneme):
    """Get an example word containing a specific phoneme in Portuguese"""
    phoneme_examples = {
        "a": "água",
        "b": "bola",
        "c": "casa",
        "d": "dedo",
        "e": "escola",
        "f": "faca",
        "g": "gato",
        "h": "hotel",
        "i": "ilha",
        "j": "janela",
        "k": "kilo",
        "l": "lua",
        "m": "mapa",
        "n": "navio",
        "o": "ovo",
        "p": "pato",
        "q": "queijo",
        "r": "rato",
        "s": "sapo",
        "t": "teto",
        "u": "uva",
        "v": "vaca",
        "w": "windsurf",
        "x": "xadrez",
        "y": "yoga",
        "z": "zebra",
        "ch": "chave",
        "lh": "alho",
        "nh": "ninho",
        "rr": "carro"
    }

    return phoneme_examples.get(phoneme.lower(), "")

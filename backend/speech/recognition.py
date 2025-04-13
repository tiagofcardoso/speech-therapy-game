import speech_recognition as sr
import logging
import tempfile
import os
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def recognize_speech(audio_file):
    """
    Reconhece fala a partir de dados de áudio usando serviços de STT

    Args:
        audio_file: Arquivo de áudio para processamento

    Returns:
        str: Texto reconhecido ou mensagem de erro
    """
    try:
        # Criar caminho para arquivo temporário
        temp_path = None

        # Se for um objeto de arquivo do Flask
        if hasattr(audio_file, 'save'):
            temp_path = f"/tmp/speech_{os.urandom(8).hex()}.wav"
            audio_file.save(temp_path)
            file_path = temp_path

            # Converter para WAV usando pydub se necessário
            try:
                audio = AudioSegment.from_file(temp_path)
                wav_path = f"{temp_path}.wav"
                audio.export(wav_path, format="wav")
                file_path = wav_path
                logger.info(f"Convertido áudio para WAV: {wav_path}")
            except Exception as convert_error:
                logger.warning(
                    f"Não foi possível converter o áudio: {convert_error}")
        else:
            # É já um caminho de arquivo
            file_path = audio_file

        recognizer = sr.Recognizer()

        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)

        # Usar reconhecimento da Google com idioma Português do Brasil
        recognized_text = recognizer.recognize_google(
            audio_data, language='pt-BR')
        logger.info(f"Texto reconhecido: '{recognized_text}'")

        # Quando o reconhecimento falha com texto vazio ou baixa confiança:
        if not recognized_text or recognized_text.strip() == "":
            logger.warning("STT não reconheceu nenhum texto")
            return "Texto não reconhecido"

        # Se a confiança for muito baixa, também consideramos como falha
        confidence = 0.5  # Placeholder for confidence value
        if confidence < 0.4:  # Valor de threshold para confiança
            logger.warning(
                f"STT reconheceu texto com baixa confiança: {confidence}")
            return "Texto não reconhecido"

        # Limpar arquivos temporários
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            if os.path.exists(f"{temp_path}.wav"):
                os.remove(f"{temp_path}.wav")

        return recognized_text

    except sr.UnknownValueError:
        logger.warning("Não foi possível entender o áudio")
        return "Texto não reconhecido"
    except sr.RequestError as e:
        logger.error(f"Erro no serviço de reconhecimento: {e}")
        return "Texto não reconhecido"
    except Exception as e:
        logger.error(f"Erro no reconhecimento de fala: {str(e)}")
        return "Texto não reconhecido"


def evaluate_pronunciation(user_input, correct_phrase):
    # Simple evaluation logic: compare user input with the correct phrase
    return user_input.lower() == correct_phrase.lower()

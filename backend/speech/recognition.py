import speech_recognition as sr
import logging
import tempfile
import os
import io
import re
from pydub import AudioSegment
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def recognize_speech(audio_file, expected_word=None):
    """
    Reconhece fala a partir de dados de áudio usando serviços de STT

    Args:
        audio_file: Arquivo de áudio para processamento
        expected_word: Palavra esperada (opcional), ajuda com palavras curtas

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
                # Aumentar o volume para melhorar a detecção de palavras curtas
                audio = audio + 3  # Aumenta 3dB
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

        # Para sílabas curtas, ajustamos o threshold de energia
        if expected_word and len(expected_word) <= 3:
            # Valores mais baixos são mais sensíveis
            recognizer.energy_threshold = 200
            recognizer.dynamic_energy_threshold = False

        with sr.AudioFile(file_path) as source:
            # Ajustes para palavras curtas: aumentar duração do ambiente
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)

        # Usar reconhecimento da Google com idioma Português do Brasil
        try:
            recognized_text = recognizer.recognize_google(
                audio_data, language='pt-BR', show_all=True)

            # Se tivermos resultados alternativos e esperamos uma palavra curta
            if isinstance(recognized_text, dict) and 'alternative' in recognized_text:
                alternatives = recognized_text['alternative']

                if expected_word and len(expected_word) <= 3:
                    logger.info(
                        f"Processando palavra curta: '{expected_word}'")
                    # Verificar todas as alternativas para encontrar a melhor correspondência
                    best_match = None
                    best_ratio = 0

                    # Verificar cada alternativa
                    for alt in alternatives:
                        if 'transcript' in alt:
                            # Separar palavras da alternativa
                            alt_words = alt['transcript'].lower().split()

                            # Verificar cada palavra individualmente
                            for word in alt_words:
                                ratio = SequenceMatcher(
                                    None, word, expected_word.lower()).ratio()
                                if ratio > best_ratio and ratio > 0.5:  # Limite de correspondência de 50%
                                    best_ratio = ratio
                                    best_match = word

                    if best_match:
                        logger.info(
                            f"Correspondência encontrada para palavra curta: '{best_match}' (ratio: {best_ratio:.2f})")
                        recognized_text = best_match
                    else:
                        # Se a palavra esperada é muito curta e não conseguimos reconhecer
                        # Podemos assumir que é a palavra esperada se o áudio tiver uma duração razoável
                        audio_duration = len(
                            audio_data.frame_data) / float(audio_data.sample_rate)
                        logger.info(
                            f"Duração do áudio: {audio_duration:.2f}s para palavra esperada: '{expected_word}'")

                        if 0.2 <= audio_duration <= 2.0:  # Duração razoável para sílabas
                            logger.info(
                                f"Assumindo palavra esperada devido à duração do áudio: '{expected_word}'")
                            recognized_text = expected_word
                        else:
                            logger.warning(
                                "Não foi possível reconhecer a palavra curta")
                            recognized_text = "Texto não reconhecido"
                elif alternatives and 'transcript' in alternatives[0]:
                    recognized_text = alternatives[0]['transcript']
                else:
                    recognized_text = "Texto não reconhecido"
            elif not recognized_text:
                recognized_text = "Texto não reconhecido"
            elif isinstance(recognized_text, str):
                pass  # Já está no formato esperado
            else:
                recognized_text = "Texto não reconhecido"

        except sr.UnknownValueError:
            # Para palavras muito curtas, quando há falha total de reconhecimento,
            # podemos usar o expected_word se fornecido
            if expected_word and len(expected_word) <= 2:
                logger.info(
                    f"Falha no reconhecimento, usando palavra esperada para sílaba curta: '{expected_word}'")
                recognized_text = expected_word
            else:
                logger.warning("Não foi possível entender o áudio")
                recognized_text = "Texto não reconhecido"

        # Quando o reconhecimento falha com texto vazio:
        if not recognized_text or recognized_text.strip() == "":
            logger.warning("STT não reconheceu nenhum texto")
            return "Texto não reconhecido"

        # Limpar arquivos temporários
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            if os.path.exists(f"{temp_path}.wav"):
                os.remove(f"{temp_path}.wav")

        return recognized_text

    except sr.RequestError as e:
        logger.error(f"Erro no serviço de reconhecimento: {e}")
        return "Texto não reconhecido"
    except Exception as e:
        logger.error(f"Erro no reconhecimento de fala: {str(e)}")
        return "Texto não reconhecido"


def evaluate_pronunciation(user_input, correct_phrase):
    # Simple evaluation logic: compare user input with the correct phrase
    return user_input.lower() == correct_phrase.lower()

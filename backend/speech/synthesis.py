import os
import tempfile
import subprocess
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def synthesize_speech(text, voice="pt-br", rate=1.0, pitch=1.0):
    """
    Synthesize speech from text using espeak
    
    Args:
        text: Text to synthesize
        voice: Voice to use (default: pt-br)
        rate: Speaking rate (default: 1.0)
        pitch: Voice pitch (default: 1.0)
        
    Returns:
        Binary audio data or None if synthesis failed
    """
    try:
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        # Calculate espeak speed (words per minute)
        # Default is 175, higher numbers = faster speech
        wpm = int(175 * rate)
        
        # Build command
        cmd = [
            "espeak-ng",
            "-v", voice,
            "-s", str(wpm),
            "-p", str(int(pitch * 50)),  # pitch 0-99
            "-w", output_path,
            text
        ]
        
        # Run espeak
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Convert output to better quality with ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as final_file:
            final_path = final_file.name
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", output_path,
            "-ar", "44100",  # Sample rate
            "-ac", "2",      # Stereo
            "-y",            # Overwrite output
            final_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        
        # Read the audio data
        with open(final_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up temporary files
        os.unlink(output_path)
        os.unlink(final_path)
        
        return audio_data
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {str(e)}")
        return None

def get_available_voices():
    import pyttsx3

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    return [(voice.id, voice.name) for voice in voices]

def set_voice(voice_id):
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty('voice', voice_id)

def get_example_word_for_phoneme(phoneme):
    """Return an example word containing the phoneme"""
    examples = {
        'r': 'rato',
        'rr': 'carro',
        'l': 'lado',
        'lh': 'folha',
        'nh': 'ninho',
        's': 'sapo',
        'z': 'casa',
        'ch': 'chuva',
        'j': 'janela',
        # Add more examples for other phonemes
    }
    return examples.get(phoneme.lower(), phoneme + "a")
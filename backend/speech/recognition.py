import speech_recognition as sr
import io
import os
import tempfile

def recognize_speech(audio_data):
    """
    Process audio data and return recognized text using Google's Speech Recognition API
    
    Parameters:
    audio_data (bytes): Audio data in bytes format
    
    Returns:
    str: Recognized text or error message
    """
    recognizer = sr.Recognizer()
    
    try:
        # Save audio data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name
        
        # Load the audio file
        with sr.AudioFile(temp_audio_path) as source:
            # Adjust for ambient noise and record
            audio = recognizer.record(source)
        
        # Use Google's Speech Recognition
        text = recognizer.recognize_google(audio)
        
        # Clean up the temporary file
        os.remove(temp_audio_path)
        
        return text
    
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Speech recognition error: {str(e)}"
    except Exception as e:
        return f"Error processing audio: {str(e)}"

def evaluate_pronunciation(user_input, correct_phrase):
    # Simple evaluation logic: compare user input with the correct phrase
    return user_input.lower() == correct_phrase.lower()
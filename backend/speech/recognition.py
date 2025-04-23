import speech_recognition as sr
import logging
import tempfile
import os
import io
import re
from pydub import AudioSegment
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def recognize_speech(audio_path, expected_word=None):
    """Mock implementation for testing"""
    return expected_word or "recognized text"


def evaluate_pronunciation(user_input, correct_phrase):
    # Simple evaluation logic: compare user input with the correct phrase
    return user_input.lower() == correct_phrase.lower()

import os
import subprocess
import json
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LipsyncGenerator:
    def __init__(self, rhubarb_path=None):
        """
        Initialize the LipsyncGenerator
        
        Args:
            rhubarb_path: Path to the Rhubarb Lip Sync executable
                          If None, will try to find it in PATH
        """
        # Try to find Rhubarb executable
        self.rhubarb_path = rhubarb_path
        if not self.rhubarb_path:
            try:
                self.rhubarb_path = subprocess.check_output(
                    ["which", "rhubarb"], 
                    universal_newlines=True
                ).strip()
            except subprocess.SubprocessError:
                self.rhubarb_path = None
        
        self.installed = self.rhubarb_path is not None
        if not self.installed:
            logger.warning("Rhubarb Lip Sync not found. Lipsync generation will use fallback method.")
    
    def generate_lipsync(self, audio_file, text=None):
        """
        Generate lipsync data from an audio file
        
        Args:
            audio_file: Path to the audio file
            text: Optional transcript of the audio (improves accuracy)
            
        Returns:
            List of lipsync events with timing and viseme information
        """
        if not self.installed:
            return self._generate_fallback_lipsync(audio_file, text)
        
        try:
            # Create a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Build the command
            cmd = [self.rhubarb_path, "-o", output_path, "--format", "json"]
            
            # Add text file if provided (improves accuracy)
            if text:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as text_file:
                    text_file.write(text.encode('utf-8'))
                    text_file_path = text_file.name
                cmd.extend(["--dialogfile", text_file_path])
            
            # Add the audio file
            cmd.append(audio_file)
            
            # Run Rhubarb
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Read the output JSON
            with open(output_path, 'r') as f:
                lipsync_data = json.load(f)
            
            # Clean up temporary files
            os.unlink(output_path)
            if text:
                os.unlink(text_file_path)
            
            # Format the data for the frontend
            formatted_data = []
            for mouth_cue in lipsync_data.get('mouthCues', []):
                formatted_data.append({
                    'start': mouth_cue.get('start', 0),
                    'end': mouth_cue.get('end', 0),
                    'value': mouth_cue.get('value', 'X')  # X is neutral viseme
                })
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error generating lipsync with Rhubarb: {str(e)}")
            return self._generate_fallback_lipsync(audio_file, text)
    
    def _generate_fallback_lipsync(self, audio_file, text):
        """Generate basic lipsync data without Rhubarb"""
        try:
            if not text:
                # Without text, just create a simple animation
                return [
                    {'start': 0.0, 'end': 0.5, 'value': 'X'},  # Start with neutral
                    {'start': 0.5, 'end': 1.0, 'value': 'A'},  # Open mouth
                    {'start': 1.0, 'end': 1.5, 'value': 'X'}   # Back to neutral
                ]
            
            # With text, create a simple animation based on the text
            # This is very basic and doesn't account for actual speech timing
            formatted_data = []
            avg_phoneme_duration = 0.15  # seconds per phoneme (approximate)
            current_time = 0.0
            
            # Simple mapping from letters to visemes
            letter_to_viseme = {
                'a': 'A', 'á': 'A', 'à': 'A', 'ã': 'A', 'â': 'A',
                'e': 'E', 'é': 'E', 'ê': 'E',
                'i': 'I', 'í': 'I',
                'o': 'O', 'ó': 'O', 'ô': 'O', 'õ': 'O',
                'u': 'U', 'ú': 'U',
                'b': 'B', 'p': 'B', 'm': 'B',
                'f': 'F', 'v': 'F',
                's': 'S', 'z': 'S', 'ç': 'S',
                't': 'D', 'd': 'D', 'n': 'D',
                'r': 'R', 'l': 'L',
                ' ': 'X',  # Space = neutral
            }
            
            # Generate visemes based on text
            for char in text.lower():
                viseme = letter_to_viseme.get(char, 'X')
                
                # Skip consecutive identical visemes
                if formatted_data and formatted_data[-1]['value'] == viseme:
                    formatted_data[-1]['end'] = current_time + avg_phoneme_duration
                else:
                    formatted_data.append({
                        'start': current_time,
                        'end': current_time + avg_phoneme_duration,
                        'value': viseme
                    })
                
                current_time += avg_phoneme_duration
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error generating fallback lipsync: {str(e)}")
            return [{'start': 0.0, 'end': 1.0, 'value': 'A'}]  # Default animation
    
    def generate_lipsync_for_phoneme(self, phoneme):
        """
        Generate static lipsync data for a specific phoneme
        
        Args:
            phoneme: The phoneme to visualize
            
        Returns:
            Viseme code for the phoneme
        """
        # Phoneme to viseme mapping
        phoneme_to_viseme = {
            # Vowels
            'a': 'A', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'U',
            'á': 'A', 'é': 'E', 'í': 'I', 'ó': 'O', 'ú': 'U',
            'â': 'A', 'ê': 'E', 'î': 'I', 'ô': 'O', 'û': 'U',
            'ã': 'A', 'õ': 'O',
            
            # Consonants
            'b': 'B', 'p': 'B', 'm': 'B',
            'f': 'F', 'v': 'F',
            'd': 'D', 't': 'D', 'n': 'D',
            's': 'S', 'z': 'S',
            'l': 'L',
            'r': 'R',
            'k': 'C', 'g': 'C',
            'x': 'X'  # Default/neutral
        }
        
        # Map the first character of the phoneme to a viseme
        phoneme_char = phoneme[0].lower() if phoneme else 'x'
        return phoneme_to_viseme.get(phoneme_char, 'X')
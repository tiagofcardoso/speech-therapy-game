from typing import List, Dict
import json
import os
from config import OPENAI_API_KEY
from utils.logger import ai_logger
from ai.openai_client import create_openai_client

class GameDesignerAgent:
    """
    Responsible for designing speech therapy exercises and games.
    Generates appropriate exercises for the child's level and needs.
    """
    def __init__(self):
        """Initialize game designer agent"""
        # Substituir inicialização antiga
        self.client = create_openai_client()
        
        if not self.client:
            print("Aviso: Cliente OpenAI não disponível. Modo offline ativado.")
            ai_logger.log_agent_call("GameDesignerAgent", "__init__", 
                                  output_data={"status": "offline", "reason": "Cliente não inicializado"})
        else:
            print("Cliente OpenAI inicializado com sucesso")
            ai_logger.log_agent_call("GameDesignerAgent", "__init__", 
                                  output_data={"status": "success", "model": "GPT-4o"})
        
        self.model = "GPT-4o"
    
    def create_exercises(self, difficulty: str, count: int = 5) -> List[Dict]:
        """
        Create speech therapy exercises based on difficulty level
        
        Parameters:
        difficulty (str): Difficulty level (beginner, intermediate, advanced)
        count (int): Number of exercises to create
        
        Returns:
        List[Dict]: List of exercise objects
        """
        ai_logger.log_agent_call("GameDesignerAgent", "create_exercises", 
                              input_data={"difficulty": difficulty, "count": count})
        
        if not self.client:
            print("AI client not available. Returning fallback exercises.")
            fallback_exercises = [
                {
                    "word": "cat",
                    "prompt": "This animal says meow",
                    "hint": "Start with a 'k' sound",
                    "visual_cue": "A furry pet with whiskers"
                },
                {
                    "word": "dog",
                    "prompt": "This animal says woof",
                    "hint": "Start with a 'd' sound",
                    "visual_cue": "A friendly pet that barks"
                },
                {
                    "word": "sun",
                    "prompt": "It shines in the sky during the day",
                    "hint": "Start with an 's' sound",
                    "visual_cue": "A bright yellow circle in the sky"
                },
                {
                    "word": "ball",
                    "prompt": "A round toy you can throw and catch",
                    "hint": "Start with a 'b' sound",
                    "visual_cue": "A round object that bounces"
                },
                {
                    "word": "hat",
                    "prompt": "You wear this on your head",
                    "hint": "Start with a 'h' sound",
                    "visual_cue": "Something you put on your head"
                }
            ][:count]
            ai_logger.log_agent_call("GameDesignerAgent", "create_exercises", 
                                  output_data={"exercises_count": len(fallback_exercises)})
            return fallback_exercises
        
        prompt = f"""
        Create {count} speech therapy exercises for children at {difficulty} level.
        Each exercise should include:
        1. A target word to pronounce
        2. A prompt to help the child understand the word
        3. A hint about how to pronounce it correctly
        4. A visual cue description

        Return the response as a list of JSON objects with keys:
        word, prompt, hint, visual_cue

        Difficulty guidelines:
        - beginner: Simple 1-2 syllable words with basic sounds
        - intermediate: 2-3 syllable words with more complex sounds
        - advanced: Multi-syllable words with challenging sound combinations
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a speech therapist who creates effective exercises for children."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            exercises = json.loads(content).get("exercises", [])
            
            # Ensure we have the right number of exercises
            ai_logger.log_agent_call("GameDesignerAgent", "create_exercises", 
                                  output_data={"exercises_count": len(exercises)})
            return exercises[:count]
            
        except Exception as e:
            print(f"Error creating exercises: {e}")
            ai_logger.log_agent_call("GameDesignerAgent", "create_exercises", 
                                  error=str(e))
            # Return fallback exercises if API call fails
            fallback_exercises = [
                {
                    "word": "cat",
                    "prompt": "This animal says meow",
                    "hint": "Start with a 'k' sound",
                    "visual_cue": "A furry pet with whiskers"
                },
                {
                    "word": "dog",
                    "prompt": "This animal says woof",
                    "hint": "Start with a 'd' sound",
                    "visual_cue": "A friendly pet that barks"
                },
                {
                    "word": "sun",
                    "prompt": "It shines in the sky during the day",
                    "hint": "Start with an 's' sound",
                    "visual_cue": "A bright yellow circle in the sky"
                },
                {
                    "word": "ball",
                    "prompt": "A round toy you can throw and catch",
                    "hint": "Start with a 'b' sound",
                    "visual_cue": "A round object that bounces"
                },
                {
                    "word": "hat",
                    "prompt": "You wear this on your head",
                    "hint": "Start with a 'h' sound",
                    "visual_cue": "Something you put on your head"
                }
            ][:count]
            ai_logger.log_agent_call("GameDesignerAgent", "create_exercises", 
                                  output_data={"exercises_count": len(fallback_exercises)})
            return fallback_exercises
    
    def generate_exercise(self, difficulty, age, focus_area):
        """
        Placeholder method - in a real implementation this would call the OpenAI API
        """
        if not self.client:
            return {
                "title": "Example Exercise (AI Not Available)",
                "description": "This is a placeholder exercise because the OpenAI API is not configured.",
                "difficulty": difficulty,
                "instructions": "Speak the following words clearly...",
                "words": ["cat", "dog", "house", "tree", "ball"]
            }
            
        # Resto da implementação...
from openai import OpenAI
import os
import random
import json

class GameGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.difficulty_levels = ["beginner", "intermediate", "advanced"]
        self.current_games = {}
    
    def create_game(self, user_id, difficulty=None):
        # If no difficulty specified, determine based on user history
        if not difficulty:
            difficulty = self._get_user_difficulty(user_id)
        
        # Generate game content based on difficulty
        game_content = self._generate_content(difficulty)
        
        # Store game state
        self.current_games[user_id] = {
            "difficulty": difficulty,
            "content": game_content,
            "current_index": 0,
            "score": 0
        }
        
        # Return initial game state
        return {
            "game_id": random.randint(1000, 9999),
            "difficulty": difficulty,
            "first_word": game_content[0]["word"],
            "prompt": game_content[0]["prompt"],
            "hint": game_content[0]["hint"]
        }
    
    def _get_user_difficulty(self, user_id):
        # In a real app, this would query the user's history
        # For now, default to beginner
        return "beginner"
    
    def _generate_content(self, difficulty):
        try:
            # Use OpenAI to generate game content using Model Context Protocol
            system_prompt = """You are a speech therapy game designer specialized in creating pronunciation exercises for children.
            
# CONTEXT
You are assisting a speech therapy application that helps children practice pronunciation.
The exercises should be appropriate for the specified difficulty level and focus on sounds that children commonly struggle with.

# EXAMPLES
For beginner level:
[
  {
    "word": "cat",
    "prompt": "This animal says 'meow'",
    "hint": "Start with a 'k' sound",
    "challenge": "The 'c' sound can be confused with 's' for beginners"
  }
]

For intermediate level:
[
  {
    "word": "yellow",
    "prompt": "The color of the sun",
    "hint": "Pay attention to the 'l' sound",
    "challenge": "The double 'l' requires proper tongue positioning"
  }
]

# TASK
Generate 5 pronunciation exercises for the specified difficulty level.
Each exercise must include:
1. "word": The target word to pronounce
2. "prompt": A sentence or clue about the word
3. "hint": A specific tip for correct pronunciation
4. "challenge": Why this word might be difficult for children

# OUTPUT FORMAT
Respond with a JSON array only. No additional text or explanations.
"""
            
            user_prompt = f"Create pronunciation exercises for {difficulty} level."
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Try to parse the JSON response
            try:
                content_str = response.choices[0].message.content
                content_json = json.loads(content_str)
                # Extract the exercises array if wrapped in another object
                if isinstance(content_json, dict) and "exercises" in content_json:
                    return content_json["exercises"]
                elif isinstance(content_json, list):
                    return content_json
                else:
                    print("Unexpected JSON structure from OpenAI response")
                    raise ValueError("Invalid response format")
            except json.JSONDecodeError:
                print("Failed to parse JSON from OpenAI response")
                raise
                
            # Fallback content based on difficulty
            if difficulty == "beginner":
                return [
                    {"word": "cat", "prompt": "This animal says 'meow'", "hint": "Start with a 'k' sound"},
                    {"word": "dog", "prompt": "This animal says 'woof'", "hint": "End with a 'g' sound"},
                    {"word": "ball", "prompt": "A round toy you can throw", "hint": "Focus on the 'b' sound"},
                    {"word": "sun", "prompt": "It shines during the day", "hint": "Make a clear 's' sound"},
                    {"word": "hat", "prompt": "You wear it on your head", "hint": "End with a clear 't' sound"}
                ]
            elif difficulty == "intermediate":
                return [
                    {"word": "rabbit", "prompt": "This animal hops around", "hint": "Focus on the 'r' sound"},
                    {"word": "yellow", "prompt": "The color of the sun", "hint": "Pay attention to the 'l' sound"},
                    {"word": "spider", "prompt": "An insect with eight legs", "hint": "Practice the 'sp' blend"},
                    {"word": "window", "prompt": "You can see through it", "hint": "Notice the 'w' sound at the end"},
                    {"word": "banana", "prompt": "A yellow fruit", "hint": "Stress the middle syllable"}
                ]
            else:  # advanced
                return [
                    {"word": "rhinoceros", "prompt": "A large animal with a horn", "hint": "Break it down: rye-nos-er-us"},
                    {"word": "helicopter", "prompt": "A flying vehicle with blades", "hint": "Stress the 'hel' part"},
                    {"word": "refrigerator", "prompt": "Keeps food cold", "hint": "Practice the 'fr' sound in the middle"},
                    {"word": "electricity", "prompt": "Powers our lights", "hint": "Focus on the 'tr' sound"},
                    {"word": "butterfly", "prompt": "A beautiful insect with wings", "hint": "Make sure to pronounce both 't' and 'f'"}
                ]
        except Exception as e:
            print(f"Error generating content: {e}")
            # Return default content if API fails
            return [{"word": "hello", "prompt": "A greeting", "hint": "Start with 'h' sound"}]
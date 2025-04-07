from typing import Dict, Any
from ai.openai_client import create_openai_client
import json

class TutorAgent:
    def __init__(self):
        """Initialize tutor agent"""
        # Substituir inicialização antiga
        self.client = create_openai_client()
        # Resto do código...
    
    def create_instructions(self, user_profile: Dict[str, Any], difficulty: str) -> Dict[str, str]:
        """
        Create personalized instructions for the speech therapy session
        
        Parameters:
        user_profile (Dict): User profile data
        difficulty (str): Difficulty level
        
        Returns:
        Dict: Instructions object with greeting, explanation, encouragement
        """
        name = user_profile.get('name', 'friend')
        age = user_profile.get('age', 7)
        
        try:
            prompt = f"""
            Create personalized speech therapy instructions for a child named {name} who is {age} years old.
            The difficulty level is {difficulty}.
            
            Return a JSON object with these fields:
            - greeting: A personal greeting that uses the child's name
            - explanation: A simple explanation of what we'll be practicing (appropriate for a {age}-year-old)
            - encouragement: An encouraging message to motivate the child
            
            Keep the language friendly, simple, and engaging for a young child.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly speech therapist who works with children."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"Error creating instructions: {e}")
            # Return fallback instructions
            return {
                "greeting": f"Hi {name}!",
                "explanation": "Today, we're going to practice saying some words. I'll show you a word, and you can try to say it out loud.",
                "encouragement": "You're doing great! Let's have fun learning together."
            }
    
    def generate_feedback(self, recognized_text: str, target_word: str) -> Dict[str, str]:
        """
        Generate feedback based on user's spoken response
        
        Parameters:
        recognized_text (str): Text recognized from speech
        target_word (str): Target word the user should say
        
        Returns:
        Dict: Feedback object with praise, correction, tip
        """
        # Simple exact match
        is_correct = recognized_text.lower().strip() == target_word.lower().strip()
        
        # Similar word detection (simple)
        is_similar = target_word.lower() in recognized_text.lower() or recognized_text.lower() in target_word.lower()
        
        if is_correct:
            return {
                "praise": "Perfect! That's exactly right!",
                "correction": None,
                "tip": "Great pronunciation!",
                "encouragement": "Keep up the great work!"
            }
        elif is_similar:
            return {
                "praise": "Close! That was almost right.",
                "correction": f"I heard '{recognized_text}'. Try saying '{target_word}'.",
                "tip": "Try saying it a bit slower.",
                "encouragement": "You're getting better each time!"
            }
        else:
            return {
                "praise": "Good try!",
                "correction": f"I heard '{recognized_text}'. Let's try saying '{target_word}'.",
                "tip": f"Listen carefully: '{target_word}'.",
                "encouragement": "Don't worry, practice makes perfect!"
            }
from typing import Dict, Any
import uuid
from ai.openai_client import create_openai_client  # Nova importação
import httpx

from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.progression_manager_agent import ProgressionManagerAgent
from ai.agents.tutor_agent import TutorAgent

class MCPCoordinator:
    def __init__(self, db_client, openai_api_key):
        """Initialize MCP coordinator"""
        self.db = db_client
        # Substituir qualquer inicialização direta pelo novo método
        self.openai_client = create_openai_client(api_key=openai_api_key)
        
        self.agents = {
            "game_designer": GameDesignerAgent(),
            "progression_manager": ProgressionManagerAgent(),
            "tutor": TutorAgent()
        }
    
    def create_game_session(self, user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new game session for a user
        
        Parameters:
        user_id (str): User identifier
        user_profile (Dict): User profile data
        
        Returns:
        Dict: Game session data
        """
        # Determine difficulty level based on user profile
        difficulty = self.agents["progression_manager"].determine_difficulty(user_profile)
        
        # Create exercises for the session
        exercises = self.agents["game_designer"].create_exercises(difficulty)
        
        # Generate personalized instructions
        instructions = self.agents["tutor"].create_instructions(user_profile, difficulty)
        
        # Create session object
        session = {
            "session_id": str(uuid.uuid4()),
            "user_id": user_id,
            "difficulty": difficulty,
            "exercises": exercises,
            "instructions": instructions,
            "current_index": 0,
            "responses": [],
            "completed": False,
            "start_time": None,  # Will be set when session starts
            "end_time": None     # Will be set when session completes
        }
        
        return session
    
    def process_response(self, session: Dict[str, Any], recognized_text: str) -> Dict[str, Any]:
        """
        Process user's spoken response
        
        Parameters:
        session (Dict): Current game session
        recognized_text (str): Text recognized from speech
        
        Returns:
        Dict: Updated session with feedback
        """
        current_index = session.get("current_index", 0)
        exercises = session.get("exercises", [])
        
        # Check if session is already complete
        if current_index >= len(exercises):
            return {
                "session_complete": True,
                "feedback": {
                    "praise": "Great job completing all exercises!",
                    "correction": None,
                    "tip": None,
                    "encouragement": "You've finished the session!"
                }
            }
        
        # Get current exercise
        current_exercise = exercises[current_index]
        target_word = current_exercise.get("word", "")
        
        # Generate feedback
        feedback = self.agents["tutor"].generate_feedback(recognized_text, target_word)
        
        # Determine if we should move to next exercise or repeat
        is_correct = recognized_text.lower().strip() == target_word.lower().strip()
        repeat_exercise = not is_correct
        
        # Update session if moving to next exercise
        if not repeat_exercise:
            session["current_index"] = current_index + 1
            session["responses"].append({
                "exercise_index": current_index,
                "target_word": target_word,
                "recognized_text": recognized_text,
                "is_correct": is_correct
            })
        
        # Check if session is now complete
        session_complete = session["current_index"] >= len(exercises)
        if session_complete:
            session["completed"] = True
            
        # Prepare next exercise info if available
        next_exercise = None
        if not session_complete:
            next_index = session["current_index"]
            next_exercise = {
                **exercises[next_index],
                "index": next_index,
                "total": len(exercises)
            }
        
        # Return response
        return {
            "session_complete": session_complete,
            "feedback": feedback,
            "current_exercise": next_exercise,
            "repeat_exercise": repeat_exercise
        }
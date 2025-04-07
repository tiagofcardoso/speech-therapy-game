from typing import Dict, Any
from ai.openai_client import create_openai_client
from config import OPENAI_API_KEY

class ProgressionManagerAgent:
    """Agent responsible for tracking user progress and determining difficulty"""
    
    def __init__(self):
        """Initialize progression manager agent"""
        # Substituir inicialização antiga
        self.client = create_openai_client()
        self.user_history = {}
    
    def determine_difficulty(self, user_profile: Dict[str, Any]) -> str:
        """
        Determine appropriate difficulty level based on user profile
        
        Parameters:
        user_profile (Dict): User profile data
        
        Returns:
        str: Difficulty level (beginner, intermediate, advanced)
        """
        # If we have previous session data, analyze it
        if user_profile.get('history') and len(user_profile['history']) > 0:
            # For simplicity, check average score from last 3 sessions
            recent_sessions = user_profile['history'][-3:]
            avg_score = sum(session.get('score', 0) for session in recent_sessions) / len(recent_sessions)
            
            # Determine difficulty based on score
            if avg_score < 60:
                return "beginner"
            elif avg_score < 85:
                return "intermediate"
            else:
                return "advanced"
        
        # First time user or no history - use age as guideline
        age = user_profile.get('age', 7)
        
        if age < 6:
            return "beginner"
        elif age < 9:
            return "intermediate"
        else:
            return "advanced"
    
    def evaluate_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate session performance and provide feedback
        
        Parameters:
        session_data (Dict): Session data including user responses
        
        Returns:
        Dict: Evaluation results and feedback
        """
        correct_count = 0
        total_exercises = len(session_data.get('exercises', []))
        
        if total_exercises == 0:
            return {
                "score": 0,
                "feedback": "No exercises completed",
                "next_difficulty": "beginner"
            }
        
        # Count correct responses
        for exercise in session_data.get('responses', []):
            if exercise.get('is_correct', False):
                correct_count += 1
        
        score = int((correct_count / total_exercises) * 100)
        
        # Determine next difficulty
        next_difficulty = session_data.get('difficulty', 'beginner')
        if score > 85 and next_difficulty != "advanced":
            if next_difficulty == "beginner":
                next_difficulty = "intermediate"
            elif next_difficulty == "intermediate":
                next_difficulty = "advanced"
        elif score < 40 and next_difficulty != "beginner":
            if next_difficulty == "advanced":
                next_difficulty = "intermediate"
            elif next_difficulty == "intermediate":
                next_difficulty = "beginner"
        
        return {
            "score": score,
            "feedback": self._generate_feedback(score, session_data.get('difficulty', 'beginner')),
            "next_difficulty": next_difficulty
        }
    
    def _generate_feedback(self, score: int, difficulty: str) -> str:
        """
        Generate personalized feedback based on score and difficulty
        
        Parameters:
        score (int): Session score
        difficulty (str): Current difficulty level
        
        Returns:
        str: Personalized feedback message
        """
        if score >= 90:
            return "Amazing job! You're doing exceptionally well!"
        elif score >= 70:
            return "Great work! You're making good progress."
        elif score >= 50:
            return "Good effort! Keep practicing and you'll improve."
        else:
            return "Practice makes perfect! Let's keep working on these sounds."
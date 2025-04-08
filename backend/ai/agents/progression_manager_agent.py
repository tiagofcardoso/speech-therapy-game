from typing import Dict, Any


class ProgressionManagerAgent:
    def __init__(self):
        self.user_history = {}

    def determine_difficulty(self, user_profile: Dict[str, Any]) -> str:
        history = user_profile.get('history', [])
        if history:
            avg_score = sum(session.get('score', 0)
                            for session in history[-3:]) / min(len(history), 3)
            if avg_score < 60:
                return "iniciante"
            elif avg_score < 85:
                return "médio"
            return "avançado"
        age = user_profile.get('age', 7)
        if age < 6:
            return "iniciante"
        elif age < 9:
            return "médio"
        return "avançado"

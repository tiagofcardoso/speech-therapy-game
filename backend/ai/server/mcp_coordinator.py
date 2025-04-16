from typing import Dict, Any, Optional
import uuid
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
import json
import sys
from pathlib import Path

# Add project root to Python path
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    # Navigate up to speech-therapy-game
    project_root = current_dir.parent.parent.parent
    sys.path.insert(0, str(project_root))

from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.progression_manager_agent import ProgressionManagerAgent
from ai.agents.tutor_agent import TutorAgent
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MCPCoordinator:
    def __init__(self, api_key: Optional[str] = None, db_connector=None):
        """Initialize the MCP Coordinator"""
        self.logger = logging.getLogger("MCPCoordinator")
        self.db_connector = db_connector
        self.sessions = {}

        # Initialize agents
        self.agents = {
            "game_designer": GameDesignerAgent(),
            "progression": ProgressionManagerAgent(),
            "speech_evaluator": SpeechEvaluatorAgent()
        }
        # Initialize tutor last since it depends on game_designer
        self.agents["tutor"] = TutorAgent(self.agents["game_designer"])

        self.logger.info("MCPCoordinator initialized with all agents")

    @property
    def game_designer(self):
        """Property to access game_designer agent directly"""
        return self.agents["game_designer"]

    def create_game_session(self, user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new game session for a user"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())

            # Create initial game using GameDesignerAgent
            game = self.agents["game_designer"].create_game(
                user_id=user_id,
                difficulty="iniciante"  # Default to beginner for new sessions
            )

            if not game:
                raise Exception("Failed to create game")

            # Create session structure
            session = {
                "session_id": session_id,
                "user_id": user_id,
                "user_profile": user_profile,
                "game": game,
                "start_time": datetime.datetime.now().isoformat(),
                "responses": [],
                "current_index": 0,
                "completed": False
            }

            # Store session
            self.sessions[session_id] = session

            # Get initial instructions from tutor
            instructions = self.agents["tutor"].create_instructions(
                user_profile=user_profile,
                difficulty=game["difficulty"]
            )

            # Return combined session info
            return {
                "session_id": session_id,
                "game": game,
                "instructions": instructions
            }

        except Exception as e:
            self.logger.error(f"Error creating game session: {str(e)}")
            return {"error": "Failed to create game session"}

    def process_response(self, session: Dict[str, Any], recognized_text: str) -> Dict[str, Any]:
        """Process a user's response in a game session"""
        try:
            if "error" in session:
                return session

            user_id = session["user_id"]
            current_index = session["current_index"]
            exercises = session["game"]["content"]

            if session.get("completed", False):
                return {
                    "session_complete": True,
                    "feedback": {
                        "message": "A sessão já foi concluída!",
                        "encouragement": "Inicie uma nova sessão para continuar jogando!",
                        "tip": None
                    }
                }

            # Get current exercise
            current_exercise = exercises[current_index]
            expected_text = current_exercise.get("target_text", "")

            # Evaluate pronunciation using SpeechEvaluatorAgent
            speech_evaluation = self.agents["speech_evaluator"].evaluate_speech(
                recognized_text, expected_text, session.get(
                    "game", {}).get("difficulty", "medium")
            )

            # Get feedback from TutorAgent
            feedback = self.agents["tutor"].provide_feedback(
                user_id, recognized_text, speech_evaluation=speech_evaluation
            )

            # Update session with response
            session["responses"].append({
                "exercise_index": current_index,
                "recognized_text": recognized_text,
                "expected_text": expected_text,
                "evaluation": speech_evaluation,
                "timestamp": datetime.datetime.now().isoformat()
            })

            # Check completion and update session
            session["current_index"] += 1
            session_complete = session["current_index"] >= len(exercises)
            if session_complete:
                session["completed"] = True
                session["end_time"] = datetime.datetime.now().isoformat()

            # Save session if we have a database connector
            if self.db_connector:
                self.db_connector.save_session(session)

            # Prepare response
            response = {
                "session_complete": session_complete,
                "feedback": feedback,
                "next_exercise": None if session_complete else exercises[session["current_index"]]
            }

            return response

        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return {"error": "Failed to process response"}


if __name__ == "__main__":
    coordinator = MCPCoordinator()
    user_profile = {"name": "João", "age": 7}
    session = coordinator.create_game_session("user123", user_profile)
    print(json.dumps(session, indent=2, ensure_ascii=False))

    response = coordinator.process_response(session, "sol")
    print(json.dumps(response, indent=2, ensure_ascii=False))

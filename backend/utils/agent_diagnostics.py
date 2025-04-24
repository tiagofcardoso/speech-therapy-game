"""
Utility functions for diagnosing and debugging agent interactions.
"""
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


class AgentInteractionTracker:
    """
    Track and log agent interactions for diagnostic purposes.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.interactions = []
        self.current_session = None
        self.logger = logging.getLogger(__name__)

    def start_session(self, session_id: str = None, user_id: str = None):
        """Start a new tracking session"""
        if not self.enabled:
            return

        session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "interactions": [],
            "status": "active"
        }
        self.logger.info(
            f"=== AGENT INTERACTION SESSION STARTED: {session_id} ===")
        return session_id

    def log_interaction(self, from_agent: str, to_agent: str, message_type: str,
                        data: Dict[str, Any], response: Optional[Dict[str, Any]] = None):
        """Log an interaction between agents"""
        if not self.enabled:
            return

        if not self.current_session:
            self.start_session()

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "data": data
        }

        if response:
            interaction["response"] = response

        self.current_session["interactions"].append(interaction)

        # Log a summary of the interaction
        self.logger.info(
            f"[AGENT:{from_agent.upper()}] → [AGENT:{to_agent.upper()}] {message_type}")

        # For debugging, add detailed data in debug level
        try:
            self.logger.debug(
                f"Interaction data: {json.dumps(data, indent=2)}")
            if response:
                self.logger.debug(
                    f"Response: {json.dumps(response, indent=2)}")
        except:
            self.logger.debug("Could not serialize interaction data to JSON")

    def end_session(self, status: str = "completed", error: str = None):
        """End the current tracking session"""
        if not self.enabled or not self.current_session:
            return

        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["status"] = status

        if error:
            self.current_session["error"] = error

        self.interactions.append(self.current_session)

        # Log session summary
        interaction_count = len(self.current_session["interactions"])
        session_id = self.current_session["session_id"]
        self.logger.info(
            f"=== AGENT INTERACTION SESSION ENDED: {session_id} ({interaction_count} interactions) ===")

        # Reset current session
        self.current_session = None

    def get_session_summary(self, session_id: str = None) -> Dict[str, Any]:
        """Get a summary of a specific session or the current session"""
        if not self.enabled:
            return {"enabled": False}

        if session_id:
            # Find the specified session
            for session in self.interactions:
                if session["session_id"] == session_id:
                    return self._create_summary(session)
        elif self.current_session:
            # Return current session summary
            return self._create_summary(self.current_session)

        return {"error": "Session not found"}

    def _create_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of a session"""
        interactions = session.get("interactions", [])

        # Count interactions by type
        interaction_types = {}
        for interaction in interactions:
            interaction_type = interaction.get("type", "unknown")
            interaction_types[interaction_type] = interaction_types.get(
                interaction_type, 0) + 1

        # Count interactions by agent pair
        agent_pairs = {}
        for interaction in interactions:
            from_agent = interaction.get("from", "unknown")
            to_agent = interaction.get("to", "unknown")
            pair = f"{from_agent}→{to_agent}"
            agent_pairs[pair] = agent_pairs.get(pair, 0) + 1

        return {
            "session_id": session.get("session_id"),
            "user_id": session.get("user_id"),
            "start_time": session.get("start_time"),
            "end_time": session.get("end_time"),
            "status": session.get("status"),
            "interaction_count": len(interactions),
            "interaction_types": interaction_types,
            "agent_pairs": agent_pairs
        }

    def clear(self):
        """Clear all tracked interactions"""
        self.interactions = []
        self.current_session = None


# Create a singleton instance of the tracker
interaction_tracker = AgentInteractionTracker()


def track_agent_interaction(func: Callable) -> Callable:
    """
    Decorator for tracking interactions between agents.
    """
    def wrapper(*args, **kwargs):
        try:
            # Extract agents and message type if possible
            from_agent = kwargs.get("from_agent", "unknown")
            to_agent = kwargs.get("to_agent", "unknown")
            message_type = kwargs.get("message_type", "message")

            # Log the start of the interaction
            interaction_tracker.log_interaction(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                data=kwargs
            )

            # Call the original function
            response = func(*args, **kwargs)

            # Log the response
            interaction_tracker.log_interaction(
                from_agent=to_agent,
                to_agent=from_agent,
                message_type=f"{message_type}_response",
                data={},
                response=response
            )

            return response
        except Exception as e:
            logger.error(f"Error in agent interaction: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    return wrapper


# Export the singleton for use in other modules
__all__ = ["interaction_tracker", "track_agent_interaction"]

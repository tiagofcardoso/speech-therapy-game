from speech.lipsync import LipsyncGenerator
from speech.recognition import recognize_speech
from speech.synthesis import synthesize_speech, get_available_voices
from ai.server.mcp_coordinator import MCPCoordinator
from ai.agents.progression_manager_agent import ProgressionManagerAgent
from ai.agents.speech_evaluator_agent import SpeechEvaluatorAgent
from ai.agents.game_designer_agent import GameDesignerAgent
from ai.agents.tutor_agent import TutorAgent
import unittest
import pytest
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure Python can find our packages
test_dir = Path(__file__).resolve().parent
project_root = test_dir.parent  # This is the backend directory
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules using absolute imports


class TestTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Configuração inicial dos testes"""
        # Inicializar agentes
        cls.game_designer = GameDesignerAgent()
        cls.tutor = TutorAgent(cls.game_designer)
        cls.speech_evaluator = SpeechEvaluatorAgent()
        cls.progression_manager = ProgressionManagerAgent()
        cls.mcp_coordinator = MCPCoordinator()
        cls.lipsync_generator = LipsyncGenerator()

        # Perfil de teste
        cls.test_user_profile = {
            "id": "test_user_123",
            "name": "Test User",
            "age": 8
        }

    def test_1_game_designer_tools(self):
        """Testar ferramentas do GameDesignerAgent"""
        print("\n1. Testando GameDesignerAgent:")

        # Criar novo jogo
        game = self.game_designer.create_game(
            user_id=self.test_user_profile["id"],
            difficulty="iniciante",
            game_type="exercícios de pronúncia"
        )

        self.assertIsNotNone(game)
        self.assertIn("game_type", game)
        self.assertIn("content", game)
        print("✅ create_game: OK")

        # Obter exercício atual
        exercise = self.game_designer.get_current_exercise(
            self.test_user_profile["id"])
        self.assertIsNotNone(exercise)
        print("✅ get_current_exercise: OK")

        # Atualizar progresso
        self.game_designer.update_progress(
            user_id=self.test_user_profile["id"],
            score_increment=8,
            exercise_data={"accuracy": 0.8, "time_spent": 30}
        )
        print("✅ update_progress: OK")

    def test_2_tutor_tools(self):
        """Testar ferramentas do TutorAgent"""
        print("\n2. Testando TutorAgent:")

        # Criar instruções
        instructions = self.tutor.create_instructions(
            self.test_user_profile,
            "iniciante"
        )
        self.assertIsNotNone(instructions)
        self.assertIn("greeting", instructions)
        print("✅ create_instructions: OK")

        # Testar feedback
        feedback = self.tutor.provide_feedback(
            user_id=self.test_user_profile["id"],
            response="casa",
            speech_evaluation={"accuracy": 0.8}
        )
        self.assertIsNotNone(feedback)
        print("✅ provide_feedback: OK")

        # Testar pesquisa na internet
        search_results = self.tutor._search_internet(
            "exercícios terapia da fala português"
        )
        self.assertIn("results", search_results)
        print("✅ search_internet: OK")

    def test_3_speech_evaluator_tools(self):
        """Testar ferramentas do SpeechEvaluatorAgent"""
        print("\n3. Testando SpeechEvaluatorAgent:")

        # Avaliar pronúncia
        evaluation = self.speech_evaluator.evaluate_speech(
            spoken_text="casa",
            expected_text="casa",
            difficulty="medium"
        )
        self.assertIsNotNone(evaluation)
        self.assertIn("accuracy", evaluation)
        print("✅ evaluate_speech: OK")

        # Analisar progresso
        progress = self.speech_evaluator.analyze_progress(
            user_id=self.test_user_profile["id"],
            session_history=[{
                "accuracy": 0.8,
                "improvement_areas": ["r", "s"]
            }]
        )
        self.assertIsNotNone(progress)
        print("✅ analyze_progress: OK")

    def test_4_synthesis_tools(self):
        """Testar ferramentas de síntese de voz"""
        print("\n4. Testando ferramentas de síntese:")

        # Testar síntese de voz
        audio = synthesize_speech("Olá, isto é um teste.")
        self.assertIsNotNone(audio)
        print("✅ synthesize_speech: OK")

        # Testar vozes disponíveis
        voices = get_available_voices()
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        print("✅ get_available_voices: OK")

    def test_5_lipsync_tools(self):
        """Testar ferramentas de lipsync"""
        print("\n5. Testando LipsyncGenerator:")

        # Testar geração de lipsync sem Rhubarb (fallback)
        lipsync_data = self.lipsync_generator._generate_fallback_lipsync(
            audio_file=None,
            text="Olá, mundo!"
        )
        self.assertIsNotNone(lipsync_data)
        print("✅ generate_fallback_lipsync: OK")

        # Testar geração de lipsync para fonema
        viseme = self.lipsync_generator.generate_lipsync_for_phoneme("a")
        self.assertIsNotNone(viseme)
        print("✅ generate_lipsync_for_phoneme: OK")

    def test_6_mcp_coordinator_tools(self):
        """Testar ferramentas do MCPCoordinator"""
        print("\n6. Testando MCPCoordinator:")

        # Criar sessão de jogo
        session = self.mcp_coordinator.create_game_session(
            user_id=self.test_user_profile["id"],
            user_profile=self.test_user_profile
        )
        self.assertIsNotNone(session)
        self.assertIn("session_id", session)
        print("✅ create_game_session: OK")

        # Processar resposta
        response = self.mcp_coordinator.process_response(
            session=session,
            recognized_text="casa"
        )
        self.assertIsNotNone(response)
        print("✅ process_response: OK")


if __name__ == "__main__":
    unittest.main()

import pytest
import os
import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add backend to Python path
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# Mock problematic modules
sys.modules['speech'] = MagicMock()
sys.modules['speech.synthesis'] = MagicMock()
sys.modules['speech.recognition'] = MagicMock()
sys.modules['speech.synthesis'].synthesize_speech = MagicMock(
    return_value="mock_audio_data")
sys.modules['speech.recognition'].recognize_speech = MagicMock(
    return_value="recognized text")

# Add the project root to Python path to make imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mock response from OpenAI"
    return mock_response


@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock()
    yield mock_client


@pytest.fixture
def mcp_coordinator(mock_openai_response):
    with patch('ai.mcp_coordinator.OpenAI') as mock_openai:
        # Configure the mock OpenAI client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        # Mock os.getenv to return a fake API key
        with patch('ai.mcp_coordinator.os.getenv', return_value="mock-api-key"):
            # Mock logging to avoid console output during tests
            with patch('ai.mcp_coordinator.logging'):
                # Create the coordinator
                from backend.ai.server.mcp_coordinator import MCPCoordinator
                coordinator = MCPCoordinator()
                yield coordinator

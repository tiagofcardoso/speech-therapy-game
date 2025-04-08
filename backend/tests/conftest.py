import pytest
import os
import sys
import logging
from unittest.mock import MagicMock, patch

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

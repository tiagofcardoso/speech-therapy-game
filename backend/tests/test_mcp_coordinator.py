import pytest
import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Import the module being tested
from ai.server.mcp_coordinator import MCPCoordinator


@pytest.fixture
def mcp_connection():
    with patch('ai.server.mcp_coordinator.OpenAI') as mock_openai:
        # Configure the mock OpenAI client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="Connection successful"))]
        )
        mock_openai.return_value = mock_client

        # Mock os.getenv to return a fake API key
        with patch('ai.server.mcp_coordinator.os.getenv', return_value="mock-api-key"):
            # Mock logging to avoid console output during tests
            with patch('ai.server.mcp_coordinator.logging'):
                coordinator = MCPCoordinator()
                yield coordinator


def test_mcp_connection(mcp_connection):
    """Test connection to OpenAI API"""
    assert hasattr(mcp_connection, 'game_designer')
    assert mcp_connection.game_designer is not None

    # Verify game_designer is accessible both ways
    assert mcp_connection.game_designer == mcp_connection.agents["game_designer"]


def test_mcp_coordinator_initialization():
    """Test if the MCP coordinator initializes correctly with API key"""
    with patch('ai.server.mcp_coordinator.OpenAI'):
        with patch('ai.server.mcp_coordinator.os.getenv', return_value="test-api-key"):
            with patch('ai.server.mcp_coordinator.logging'):
                coordinator = MCPCoordinator()
                assert coordinator.agents is not None
                assert "game_designer" in coordinator.agents
                assert coordinator.game_designer is not None


def test_openai_client_creation():
    """Test that OpenAI client is created with the correct API key"""
    mock_openai = MagicMock()
    with patch('ai.server.mcp_coordinator.OpenAI', mock_openai):
        with patch('ai.server.mcp_coordinator.os.getenv', return_value="test-api-key"):
            with patch('ai.server.mcp_coordinator.logging'):
                coordinator = MCPCoordinator()
                assert coordinator.game_designer is not None


def test_game_creation():
    """Test that games can be created through the game designer"""
    # Create a mock response for game creation
    mock_game = {
        "title": "Test Game",
        "difficulty": "iniciante",
        "content": [
            {"type": "exercise", "target_text": "test"}
        ]
    }

    # Create the coordinator with mocked game designer
    with patch('ai.server.mcp_coordinator.GameDesignerAgent') as MockGameDesigner:
        instance = MockGameDesigner.return_value
        instance.create_game.return_value = mock_game

        with patch('ai.server.mcp_coordinator.logging'):
            coordinator = MCPCoordinator()

            # Create a game session
            session = coordinator.create_game_session(
                user_id="test_user",
                user_profile={"name": "Test User", "age": 7}
            )

            # Verify the game was created
            assert session is not None
            assert "game" in session
            assert session["game"] == mock_game
            instance.create_game.assert_called_once()

from ai.server.mcp_server import MCPServer, Message, ModelContext, Agent, Tool, ToolParam
from ai.server.mcp_coordinator import MCPSystem
import pytest
import pytest_asyncio  # Import pytest_asyncio
import os
import sys
import json
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Mock the speech module before it's imported
sys.modules['speech'] = MagicMock()
sys.modules['speech.synthesis'] = MagicMock()
sys.modules['speech.recognition'] = MagicMock()
sys.modules['speech.synthesis'].synthesize_speech = MagicMock(
    return_value="mock_audio_data")
sys.modules['speech.recognition'].recognize_speech = MagicMock(
    return_value="recognized text")

# Now import your modules


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client"""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content=json.dumps({"result": "success", "data": "mock response"})))]
    )
    return mock_client


@pytest.fixture
def mock_db_connector():
    """Create a mock database connector with async methods"""
    connector = MagicMock()  # Keep the main connector as MagicMock

    # --- Change these to AsyncMock ---
    connector.get_user = AsyncMock(return_value={
                                   "id": "user123", "name": "Test User", "age": 8, "preferences": {}, "age_group": "crianças"})
    connector.save_session = AsyncMock()
    # --- End Change ---

    # Keep this synchronous if it's not awaited in the code being tested
    connector.get_session = MagicMock(return_value={
        "session_id": "session123",
        "user_id": "user123",
        "completed": False
    })

    # Add mock for store_search_history if it's awaited
    connector.store_search_history = AsyncMock()

    return connector


@pytest_asyncio.fixture  # Use pytest_asyncio.fixture
async def mcp_system(mock_openai, mock_db_connector):
    """Create an MCP system with mocked dependencies"""
    with patch('ai.server.mcp_coordinator.OpenAI', return_value=mock_openai):
        with patch('ai.server.mcp_coordinator.os.getenv', return_value="mock-api-key"):
            # Create the system
            system = MCPSystem(api_key="mock-api-key",
                               db_connector=mock_db_connector)

            # Mock initialize_agents to avoid actual agent initialization
            system.initialize_agents = AsyncMock()
            await system.initialize_agents()

            # Create simplified mocked agent instances
            # Ensure these instances are attached to the system object
            system._game_designer_instance = MagicMock()
            system._game_designer_instance.create_game = AsyncMock(return_value={
                "game_id": "game123",
                "title": "Test Game",
                "difficulty": "médio",
                "content": [{"text": "Test exercise", "type": "pronunciation"}]
            })

            system._speech_evaluator_instance = MagicMock()
            system._speech_evaluator_instance.evaluate_speech = AsyncMock(return_value={
                "accuracy": 0.8,
                "score": 8,
                "strengths": ["Good pronunciation"],
                "improvement_areas": ["Work on intonation"]
            })

            system._tutor_instance = MagicMock()
            system._tutor_instance.provide_feedback = AsyncMock(return_value={
                "text": "Good job! Keep practicing.",
                "correct": True,
                "score": 8
            })

            return system  # Return the system instance directly


@pytest.mark.asyncio
async def test_mcp_server_initialization(mcp_system):
    """Test that the MCP server initializes correctly"""
    assert mcp_system.server is not None
    assert mcp_system.api_key == "mock-api-key"
    assert mcp_system.db_connector is not None


@pytest.mark.asyncio
async def test_agent_registration(mcp_system):
    """Test that agents can be registered with the server"""
    # Create a mock agent
    agent = Agent(
        name="test_agent",
        handler=AsyncMock(),
        tools=[Tool(name="test_tool", description="A test tool", parameters=[])]
    )

    # Register the agent
    mcp_system.server.register_agent(agent)

    # Verify the agent was registered
    assert "test_agent" in mcp_system.server.agents
    assert mcp_system.server.agents["test_agent"] == agent


@pytest.mark.asyncio
async def test_message_processing(mcp_system):
    """Test that messages can be processed by the server"""
    # Create a mock agent with a mock handler
    mock_handler = AsyncMock(return_value={"result": "success"})
    agent = Agent(
        name="test_agent",
        handler=mock_handler,
        tools=[Tool(name="test_tool", description="A test tool", parameters=[])]
    )

    # Register the agent
    mcp_system.server.register_agent(agent)

    # Create a message
    message = Message(
        from_agent="system",
        to_agent="test_agent",
        tool="test_tool",
        params={"param1": "value1"}
    )

    # Create a context
    context = ModelContext()

    # Process the message
    result = await mcp_system.server.process_message(message, context)

    # Verify the handler was called with the correct arguments
    mock_handler.assert_called_once()
    assert mock_handler.call_args[0][0] == message
    assert isinstance(mock_handler.call_args[0][1], ModelContext)

    # Verify the result
    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_context_management(mcp_system):
    """Test context management functions"""
    # Create a context
    context = ModelContext()

    # Test setting values
    context.set("key1", "value1")
    context.set("key2", 123)

    # Test getting values
    assert context.get("key1") == "value1"
    assert context.get("key2") == 123

    # Test has function
    assert context.has("key1")
    assert not context.has("key3")

    # Test delete function
    context.delete("key1")
    assert not context.has("key1")

    # Test get with default
    assert context.get("key3", "default") == "default"


@pytest.mark.asyncio
async def test_game_designer_handler(mcp_system):
    """Test the game designer handler"""
    # Create a context
    context = ModelContext()

    # Create a message
    message = Message(
        from_agent="system",
        to_agent="game_designer",
        tool="create_game",
        params={
            "user_id": "user123",
            "difficulty": "médio",
            "game_type": "pronunciation",
            "age_group": "crianças"
        }
    )

    # Register a mock game_designer_agent
    agent = Agent(
        name="game_designer",
        handler=mcp_system._game_designer_handler,
        tools=[Tool(
            name="create_game",
            description="Creates a game",
            parameters=[
                ToolParam(name="user_id", type="string",
                          description="The user ID"),
                ToolParam(name="difficulty", type="string",
                          description="The difficulty level")
            ]
        )]
    )

    mcp_system.server.register_agent(agent)

    # Process the message
    result = await mcp_system.server.process_message(message, context)

    # Verify the result
    assert "game_id" in result
    assert result["title"] == "Test Game"
    assert result["difficulty"] == "médio"

    # Verify the game was stored in context
    assert context.has("current_game_user123")


@pytest.mark.asyncio
async def test_create_interactive_session(mcp_system):
    """Test the create_interactive_session workflow"""
    # Mock the process_message method to return expected values
    mcp_system.server.process_message = AsyncMock()

    # For select_persona
    persona_result = {"style": "animado", "voice": "Ines", "emoji": "🌟"}
    # For determine_difficulty
    difficulty_result = "médio"
    # For create_game
    game_result = {
        "game_id": "game123",
        "title": "Test Game",
        "difficulty": "médio",
        "content": [{"text": "Test exercise", "type": "pronunciation"}]
    }
    # For create_instructions
    instructions_result = {
        "text": "Welcome to the game!", "audio": "base64audio"}

    # Configure mock to return different values based on the message
    def mock_process_message(message, context):
        if message.tool == "select_persona":
            return persona_result
        elif message.tool == "determine_difficulty":
            return difficulty_result
        elif message.tool == "create_game":
            return game_result
        elif message.tool == "create_instructions":
            return instructions_result
        return {}

    mcp_system.server.process_message.side_effect = mock_process_message

    # Call the method
    session = await mcp_system.create_interactive_session("user123")

    # Verify the result
    assert session["session_id"] is not None
    assert session["user_id"] == "user123"
    assert session["difficulty"] == "médio"
    assert session["persona"] == persona_result
    assert session["game_data"] == game_result
    assert session["instructions"] == instructions_result

    # Verify the session was saved
    mcp_system.db_connector.save_session.assert_called_once()


@pytest.mark.asyncio
async def test_process_user_response(mcp_system):
    """Test the process_user_response workflow"""
    # Mock the process_message method to return expected values
    mcp_system.server.process_message = AsyncMock()

    # For evaluate_speech

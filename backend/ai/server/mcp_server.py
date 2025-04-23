import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable


class ToolParam:
    """Parameter definition for a tool"""

    def __init__(self, name: str, type: str, description: str, optional: bool = False):
        self.name = name
        self.type = type
        self.description = description
        self.optional = optional


class Tool:
    """Tool definition for an agent"""

    def __init__(self, name: str, description: str, parameters: List[ToolParam]):
        self.name = name
        self.description = description
        self.parameters = parameters


class Message:
    """Message for communication between agents"""

    def __init__(self, from_agent: str, to_agent: str, tool: str, params: Dict[str, Any]):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.tool = tool
        self.params = params


class ModelContext:
    """Context for storing and retrieving data across agent calls"""

    def __init__(self):
        self.id = str(uuid.uuid4())
        self._data = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        if key in self._data:
            del self._data[key]


class Agent:
    """Agent definition"""

    def __init__(self, name: str, handler: Callable[[Message, ModelContext], Awaitable[Any]], tools: List[Tool]):
        self.name = name
        self.handler = handler
        self.tools = tools


class MCPServer:
    """Model Context Protocol Server"""

    def __init__(self):
        self.agents = {}  # Dictionary to store agent handlers
        self.logger = logging.getLogger(__name__)

    def register_handler(self, agent_name: str, handler_func: Callable):
        """Register a handler function for an agent"""
        self.agents[agent_name] = handler_func
        self.logger.info(f"Registered handler for agent: {agent_name}")

    async def process_message(self, message: Message, context: ModelContext) -> Any:
        """Process a message by routing it to the appropriate agent handler"""
        if message.to_agent not in self.agents:
            raise ValueError(
                f"No handler registered for agent: {message.to_agent}")

        return await self.agents[message.to_agent](message, context)

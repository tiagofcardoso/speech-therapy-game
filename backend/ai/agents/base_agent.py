"""
Base agent class with common functionality and enhanced logging.
"""
import logging
import datetime
import os  # Add the missing import
from typing import Dict, Any, Optional, List
from openai import OpenAI
from utils.agent_logger import get_agent_logger, log_agent_call


class BaseAgent:
    """Base class for all agents with standardized logging"""

    def __init__(self, name: str = None, client=None):
        """Initialize the base agent with logging setup and optional OpenAI client"""
        # Get class name without 'Agent' suffix
        if name:
            self.agent_name = name.upper()
        else:
            self.agent_name = self.__class__.__name__.replace(
                'Agent', '').upper()

        # Set up logger
        self.logger = get_agent_logger(self.agent_name)
        self.logger.info(f"Agent initialized")

        self.client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @log_agent_call
    async def initialize(self, context=None) -> bool:
        """Initialize agent - to be overridden by subclasses"""
        self.logger.info(f"Base initialization complete")
        return True

    def log_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an agent action with standardized formatting

        Args:
            action: Action being performed
            details: Optional details to include in the log
        """
        if details:
            detail_str = " - " + \
                ", ".join(f"{k}={v}" for k, v in details.items())
        else:
            detail_str = ""

        self.logger.info(f"{action}{detail_str}")

    def __str__(self) -> str:
        """String representation of the agent"""
        return f"{self.agent_name} Agent"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return list of tool definitions this agent supports"""
        return []

    def _track_metric(self, name: str, value: Any, metadata: Dict[str, Any] = None):
        """Track agent-specific metrics"""
        self.logger.info(f"Metric - {name}: {value} {metadata or ''}")
        # Could be extended to send metrics to monitoring system

    async def execute_with_context(self, method_name: str, context, **kwargs):
        """Execute a method with context awareness"""
        if not hasattr(self, method_name):
            raise ValueError(
                f"Method {method_name} not found in {self.__class__.__name__}")

        method = getattr(self, method_name)

        # Add context to kwargs if the method accepts it
        import inspect
        sig = inspect.signature(method)
        if 'context' in sig.parameters:
            kwargs['context'] = context

        # Execute the method
        start_time = datetime.datetime.now()
        try:
            result = await method(**kwargs)
            # Store result in context if the call succeeds
            context.set(f"last_result_{method_name}", result)
            return result
        except Exception as e:
            # Log error and store in context
            self.logger.error(f"Error executing {method_name}: {str(e)}")
            error_info = {
                "error": str(e),
                "method": method_name,
                "timestamp": datetime.datetime.now().isoformat()
            }
            context.set(f"last_error_{method_name}", error_info)
            raise
        finally:
            # Track execution time
            execution_time = (datetime.datetime.now() -
                              start_time).total_seconds()
            self._track_metric(f"{method_name}_execution_time", execution_time)
            context.set(f"last_execution_time_{method_name}", execution_time)

    async def retry_with_backoff(self, coro, max_retries=3, base_delay=1):
        """Retry a coroutine with exponential backoff"""
        import asyncio

        retries = 0
        while True:
            try:
                return await coro
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    self.logger.error(
                        f"Failed after {max_retries} retries: {str(e)}")
                    raise

                delay = base_delay * (2 ** (retries - 1))
                self.logger.warning(
                    f"Retry {retries}/{max_retries} after {delay}s: {str(e)}")
                await asyncio.sleep(delay)

    async def with_telemetry(self, method_name, context=None, **kwargs):
        """Execute a method with full telemetry"""
        start_time = datetime.datetime.now()
        success = False
        result = None
        error = None

        try:
            method = getattr(self, method_name)
            result = await method(**kwargs)
            success = True
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Record telemetry
            telemetry = {
                "agent": self.__class__.__name__,
                "method": method_name,
                "success": success,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
                "parameters": {k: v for k, v in kwargs.items() if k != "context"},
            }

            if error:
                telemetry["error"] = error

            if context:
                # Append to telemetry list in context
                if not context.has("telemetry"):
                    context.set("telemetry", [])
                telemetry_list = context.get("telemetry")
                telemetry_list.append(telemetry)
                context.set("telemetry", telemetry_list)

            self.logger.info(
                f"Telemetry: {method_name} - {duration:.2f}s - {'✓' if success else '✗'}")

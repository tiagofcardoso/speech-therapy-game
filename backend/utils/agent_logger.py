"""
Utility functions for standardized agent logging across the application
"""
import logging
import functools
import inspect
from typing import Optional, Callable, Any


def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Get a logger configured for a specific agent with standardized formatting.

    Args:
        agent_name: Name of the agent (e.g., "SPEECH_EVALUATOR", "GAME_DESIGNER")

    Returns:
        Logger instance configured for the agent
    """
    logger = logging.getLogger(f"agent.{agent_name.lower()}")

    # Only add the handler if it doesn't already exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [AGENT:%(agent_name)s] %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Set a filter that adds the agent_name to the LogRecord
    class AgentFilter(logging.Filter):
        def filter(self, record):
            record.agent_name = agent_name.upper()
            return True

    # Only add the filter if it's not already there
    has_filter = False
    for f in logger.filters:
        if isinstance(f, AgentFilter):
            has_filter = True
            break

    if not has_filter:
        logger.addFilter(AgentFilter())

    return logger


def log_agent_call(func: Callable) -> Callable:
    """
    Decorator to log agent method calls with standardized format

    Usage:
    @log_agent_call
    async def some_method(self, param1, param2):
        ...
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get the class name from the first argument (self)
        if len(args) > 0 and hasattr(args[0], '__class__'):
            agent_class = args[0].__class__.__name__
            agent_name = agent_class.replace('Agent', '').upper()
        else:
            agent_name = "UNKNOWN"

        logger = get_agent_logger(agent_name)
        method_name = func.__name__

        # Get parameter names and values
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        # Skip 'self' parameter
        if len(param_names) > 0 and param_names[0] == 'self':
            param_names = param_names[1:]

        # Extract values from args and kwargs
        param_values = []
        for i, name in enumerate(param_names):
            if i < len(args) - 1:  # -1 because we skip 'self'
                value = args[i + 1]
            elif name in kwargs:
                value = kwargs[name]
            else:
                continue

            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                value = f"{value[:50]}..."

            param_values.append(f"{name}={value}")

        params_str = ", ".join(param_values)

        logger.info(f"Starting {method_name}({params_str})")
        try:
            result = await func(*args, **kwargs)

            # Truncate result for logging if it's too long
            result_str = str(result)
            if len(result_str) > 100:
                result_str = f"{result_str[:100]}..."

            logger.info(f"Completed {method_name} → {result_str}")
            return result
        except Exception as e:
            logger.error(f"Error in {method_name}: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get the class name from the first argument (self)
        if len(args) > 0 and hasattr(args[0], '__class__'):
            agent_class = args[0].__class__.__name__
            agent_name = agent_class.replace('Agent', '').upper()
        else:
            agent_name = "UNKNOWN"

        logger = get_agent_logger(agent_name)
        method_name = func.__name__

        # Simplified parameter logging (just count)
        arg_count = len(args) - 1 if len(args) > 0 else 0
        kwarg_count = len(kwargs)

        logger.info(
            f"Starting {method_name} (args: {arg_count}, kwargs: {kwarg_count})")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Completed {method_name}")
            return result
        except Exception as e:
            logger.error(f"Error in {method_name}: {str(e)}")
            raise

    # Use the appropriate wrapper based on whether the function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

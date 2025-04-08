from unittest.mock import MagicMock

def mock_openai_api():
    mock_response = MagicMock()
    mock_response.choices = [{'text': 'Hello, world!'}]
    return mock_response

def mock_openai_completion_create(*args, **kwargs):
    return mock_openai_api()
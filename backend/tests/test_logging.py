from ai.agents.tools import tool_registry


@tool_registry.register(
    name='test_tool',
    description='Test tool for logging demonstration'
)
def test_function():
    return {'status': 'success', 'message': 'Tool called successfully'}


if __name__ == '__main__':
    print("Calling test tool...")
    result = tool_registry.execute('test_tool')
    print("Test completed.")
